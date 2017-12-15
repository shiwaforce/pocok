import os
import platform
import shutil
import tarfile
from subprocess import check_output, check_call
from .console_logger import ColorPrint
from .environment_utils import EnvironmentUtils
from .project_utils import ProjectUtils
from .file_utils import FileUtils
from .state import StateHolder
from .yaml_handler import YamlHandler


class PackageHandler(object):

    repo_dir = None
    working_directory = None
    project_utils = None

    def pack(self, files, project_utils, envs):
        EnvironmentUtils.check_docker()
        compose_handler = StateHolder.compose_handler
        self.repo_dir = compose_handler.repo_dir
        self.working_directory = compose_handler.get_working_directory()

        self.project_utils = project_utils

        if not os.path.exists(os.path.join(self.working_directory, "tmp_archive")):
            os.mkdir(os.path.join(self.working_directory, "tmp_archive"))

        target_file = os.path.join(self.working_directory, StateHolder.name + ".poco")
        images_file = os.path.join(self.working_directory, "tmp_archive", StateHolder.name + ".tar")
        compose_file = os.path.join(self.working_directory, "tmp_archive", "docker-compose.yml")
        poco_file = os.path.join(self.working_directory, "tmp_archive", "poco.yml")
        images = self.get_images(files)

        cmd = self.get_compose_base_cmd(docker_files=files)
        cmd.append("config")
        res = EnvironmentUtils.decode(check_output(" ".join(cmd), env=envs,
                                                   cwd=self.working_directory, shell=True))

        with open(compose_file, 'w') as stream:
            stream.write(res.replace(str(self.working_directory), "."))

        src_file = os.path.join(os.path.dirname(__file__), 'resources/poco.yml')
        shutil.copyfile(src=src_file, dst=poco_file)

        cmd = list()
        cmd.append("docker")
        cmd.append("save")
        cmd.append("-o")
        cmd.append(images_file)
        for image in images:
            cmd.append(str(image))
        res = check_call(" ".join(cmd), cwd=self.working_directory, shell=True)
        if res > 0:
            ColorPrint.exit_after_print_messages(message=res)

        with tarfile.open(target_file, "w:gz") as tar:
            tar.add(os.path.join(self.working_directory, "tmp_archive"), arcname='.')

        shutil.rmtree(os.path.join(self.working_directory, "tmp_archive"))
        ColorPrint.print_info(message='Docker environment save to ' + target_file)

    def unpack(self):
        EnvironmentUtils.check_docker()
        poco_file = None
        for file in next(os.walk(os.getcwd()))[2]:
            if file.endswith(".poco"):
                poco_file = file
                tar = tarfile.open(file)
                tar.extractall()
                tar.close()
                break
        if poco_file is None:
            ColorPrint.exit_after_print_messages(message=".poco file not exists in current directory")

        cmd = list()
        cmd.append("docker")
        cmd.append("load")
        cmd.append("-i")
        cmd.append(poco_file.rstrip("poco") + "tar")
        self.run_script(cmd=cmd)

    @staticmethod
    def get_compose_base_cmd(docker_files):
        cmd = list()
        cmd.append("docker-compose")
        for compose_file in docker_files:
            cmd.append("-f")
            cmd.append(str(compose_file))
        return cmd

    def run_script(self, cmd):
        res = check_call(" ".join(cmd), cwd=self.working_directory, shell=True)
        if res > 0:
            ColorPrint.exit_after_print_messages(message=res)

    def get_images(self, docker_files):
        res = list()
        for docker_file in docker_files:
            res.extend(self.get_image(docker_file))
        return set(res)

    def get_image(self, docker_file):
        res = list()
        compose_content = YamlHandler.read(docker_file)
        for serv in compose_content['services']:
            service = compose_content['services'][serv]
            if isinstance(service, dict) and 'image' in service:
                res.append(service['image'])
        return res

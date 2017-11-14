from .console_logger import ColorPrint
from subprocess import check_output, CalledProcessError


class CleanHandler:

    def clean(self):
        self.check_container(status="created")
        self.check_container(status="exited")
        self.check_images()
        self.check_volumes()

    def check_container(self, status):
        out = check_output(" ".join(["docker", "ps", "-qf", "status=" + str(status)]), shell=True)
        if len(out) == 0:
            ColorPrint.print_warning('No "' + str(status) + '" containers to remove.')
        else:
            ColorPrint.print_info("=== clean unused containers  ===")
            ColorPrint.print_with_lvl(message="Remove containers:\n" + str(out), lvl=1)
            try:
                self.checkout("docker", "rm", out.strip().splitlines())
            except CalledProcessError as grepexc:
                self.print_error(grepexc)

    def check_images(self):
        out = check_output(" ".join(["docker", "images", "-q"]), shell=True)
        if len(out) == 0:
            ColorPrint.print_warning('No images to remove.')
        else:
            ColorPrint.print_info("=== clean unused images  ===")
            ColorPrint.print_with_lvl(message="Remove images:\n" + str(out), lvl=1)
            try:
                self.checkout("docker", "rmi", "-f", out.strip().splitlines())
            except CalledProcessError as grepexc:
                self.print_error(grepexc)

    def check_volumes(self):
        out = check_output(" ".join(["docker", "volume", "ls", "-q"]), shell=True)
        if len(out) == 0:
            ColorPrint.print_warning('No volumes to remove.')
        else:
            ColorPrint.print_info("=== clean unused volumes  ===")
            ColorPrint.print_with_lvl(message="Remove volumes:\n" + str(out), lvl=1)
            self.checkout("docker", "volume", "rm", out.splitlines())

    def checkout(self, *args):
        command_array = list()
        for cnt, command in enumerate(args):
            if type(command) is list:
                for comm in command:
                    command_array.append(comm)
            else:
                command_array.append(command)
        try:
            check_output(" ".join(command_array), shell=True)
        except CalledProcessError as grepexc:
            self.print_error(grepexc)

    @staticmethod
    def print_error(exc):
        ColorPrint.print_error(
            "error code: " + str(exc.returncode) + " with output: " + str(exc.output))
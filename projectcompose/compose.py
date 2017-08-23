#!/usr/bin/env python
"""SF Program compose.

Usage:
  project-compose [options] config [<project>] [<plan>]
  project-compose [options] clean
  project-compose [options] init [<project>]
  project-compose [options] install [<project>] [<plan>]
  project-compose [options] up [<project>] [<plan>]
  project-compose [options] down [<project>] [<plan>]
  project-compose [options] build [<project>] [<plan>]
  project-compose [options] ps [<project>] [<plan>]
  project-compose [options] plan ls [<project>]
  project-compose [options] pull [<project>] [<plan>]
  project-compose [options] start [<project>] [<plan>]
  project-compose [options] stop [<project>] [<plan>]
  project-compose [options] log [<project>] [<plan>]
  project-compose [options] logs [<project>] [<plan>]
  project-compose [options] branch <project> <branch> [-f]
  project-compose [options] branches [<project>]

  project-compose (-h | --help)
  project-compose --version

Options:
  -h --help     Show this screen.
  -v --verbose  Print more text.
  -q --quiet    Print less text.
  --offline     Offline mode

"""
import os
import shutil
import sys
from docopt import docopt
from .abstract_command import AbstractCommand
from .services.clean_handler import CleanHandler
from .services.file_utils import FileUtils
from .services.console_logger import ColorPrint


class ProjectCompose(AbstractCommand):

    def __init__(self, home_dir=os.path.join(os.path.expanduser(path='~'), '.project-compose'), skip_docker=False,
                 argv=sys.argv[1:]):
        super(ProjectCompose, self).__init__(home_dir=home_dir, skip_docker=skip_docker, doc=__doc__, argv=argv)

    def run(self):
        #try:
        '''Parse catalog'''
        self.parse_catalog(offline=self.arguments.get("--offline"))

        if self.arguments.get('<project>') is None:
            self.arguments['<project>'] = FileUtils.get_directory_name()

        '''Handling top level commands'''
        if self.arguments.get('clean'):
            CleanHandler().clean()
            ColorPrint.exit_after_print_messages(message="Clean complete", msg_type="info")

        '''Init project utils'''
        self.init_project_utils(offline=self.arguments.get("--offline"))

        '''Get project name'''
        self.name = self.arguments.get('<project>')

        if self.arguments.get('branches'):
            self.print_branches(repo=self.get_project_repository())
            return

        if self.arguments.get('branch'):
            branch = self.arguments.get('<branch>')
            repo = self.get_project_repository()
            repo.set_branch(branch=branch, force=self.arguments.get("-f"))
            project_descriptor = self.catalog_handler.get(name=self.name)
            project_descriptor['branch'] = branch
            self.catalog_handler.set(name=self.name, modified=project_descriptor)
            ColorPrint.print_info(message="Branch changed")
            return

        if self.arguments.get('install'):
            self.get_project_repository()
            ColorPrint.print_info("Project installed")

        if self.arguments.get('init'):
            self.init()
            '''Init compose handler'''
            self.init_compose_handler(arguments=self.arguments)
            self.run_scripts(script_type="init_script")

        '''Init compose handler'''
        self.init_compose_handler(arguments=self.arguments)

        if self.arguments.get('plan') and self.arguments.get('ls'):
            self.compose_handler.get_plan_list(name=self.name)

        if self.arguments.get('config'):
            self.run_scripts(script_type="before_script")
            self.run_docker_command(commands="config")

        if self.arguments.get('build'):
            self.run_before(offline=self.arguments.get("--offline"))
            self.run_docker_command(commands="build")
            ColorPrint.print_info("Project built")

        if self.arguments.get('up') or self.arguments.get('start'):
            self.run_before(offline=self.arguments.get("--offline"))
            self.run_docker_command(commands="build")
            self.run_docker_command(commands="config")
            self.run_docker_command(commands=["up", "-d"])
            self.run_docker_command(commands="logs")
            self.run_docker_command(commands="ps")
            self.run_after()

        if self.arguments.get('down'):
            self.run_docker_command(commands=["down", "--remove-orphans"])
            ColorPrint.print_info("Project stopped")

        if self.arguments.get('ps'):
            self.run_before(offline=self.arguments.get("--offline"))
            self.run_docker_command(commands="ps")
            self.run_after()

        if self.arguments.get('pull'):
            self.run_before(offline=self.arguments.get("--offline"))
            self.run_docker_command(commands="pull")
            ColorPrint.print_info("Project pull complete")

        if self.arguments.get('stop'):
            self.run_docker_command(commands="stop")
            self.run_after()

        if self.arguments.get('logs') or self.arguments.get('log'):
            self.run_docker_command(commands=["logs", "-f"])

        #except Exception as ex:
            #ColorPrint.exit_after_print_messages(message="Unexpected error: " + type(ex).__name__ + "\n" + ex.message + "\n" + str(ex.args))

    def init(self):
        project_element = self.get_catalog(self.name)
        repo = self.get_project_repository()
        file = repo.get_file(project_element.get('file', 'project-compose.yml'))

        if not os.path.exists(file):
            src_file = os.path.join(os.path.dirname(__file__), 'services/resources/project-compose.yml')
            shutil.copyfile(src=src_file, dst=file)
            default_compose = os.path.join(os.path.dirname(file), 'docker-compose.yml')
            if not os.path.exists(default_compose):
                src_file = os.path.join(os.path.dirname(__file__), 'services/resources/docker-compose.yml')
                shutil.copyfile(src=src_file, dst=default_compose)
        ColorPrint.print_info("Project init completed")


def main():
    compose = ProjectCompose()
    compose.run()

if __name__ == '__main__':
    sys.exit(main())
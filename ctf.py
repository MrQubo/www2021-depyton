#!/usr/bin/env python3
# Python: >=3.7, <4.0

from copy import deepcopy
import functools
import logging
import os
from pathlib import Path
import sys

import click


os.environ['DOCKER_BUILDKIT'] = '1'
os.environ['COMPOSE_DOCKER_CLI_BUILD'] = '1'

source_dir = Path(__file__).resolve().parent


def ensure_path_parents(path):
    path.parent.mkdir(parents=True, exist_ok=True)


# https://github.com/pycontribs/tendo/blob/master/tendo/singleton.py
class SingleInstance:
    def __init__(self):
        import fcntl

        self.initialized = False
        self.lockfile = source_dir / '.generated' / 'ctf.lock'

        ensure_path_parents(self.lockfile)
        self.fp = self.lockfile.open('w')
        self.fp.flush()

        try:
            fcntl.lockf(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.initialized = True
        except IOError:
            click.confirm(
                '\n'.join([
                    f'Lockfile `{str(self.lockfile)}` is locked.',
                    'Do you want to continue?',
                ]),
                default=False,
                abort=True,
                err=True,
            )
            self.fp.close()

        self.lockf = fcntl.lockf
        self.LOCK_UN = fcntl.LOCK_UN

    def __del__(self):
        try:
            if not self.initialized:
                return

            self.lockf(self.fp, self.LOCK_UN)
            try:
                self.lockfile.unlink()
            except FileNotFoundError:
                pass
        except Exception as e:
            print('Error:', e)
            raise

def oxford_comma_join(l):
    assert len(l) > 0, l

    if len(l) == 1:
        return l[0]
    elif len(l) == 2:
        return ' and '.join(l)
    else:
        return ', '.join(l[:-1]) + ', and ' + l[-1]


def read_yml(filename):
    import yaml

    with open(filename, 'r') as f:
        return yaml.safe_load(f)

def write_yml(obj, filename):
    import yaml

    with open(filename, 'w') as f:
        return yaml.dump(obj, f)


@functools.lru_cache(maxsize=None)
def get_config():
    if production:
        filename = source_dir / 'config.prod.yml'
    else:
        filename = source_dir / 'config.yml'

    return read_yml(filename)

@functools.lru_cache(maxsize=None)
def get_tasks_config():
    return read_yml(source_dir / 'tasks/tasks.yml')

def get_task_dir(task):
    return source_dir / 'tasks' / task

@functools.lru_cache(maxsize=None)
def get_task_config_from_name(task):
    return read_yml(get_task_dir(task) / 'task.yml')

def is_task_dir(path):
    return path.parent == source_dir / 'tasks' and (path / 'task.yml').exists()


def ensure_ctfd_submodule():
    from subprocess import check_call

    check_call(['git', 'submodule', 'update', '--init', 'CTFd/'], cwd=source_dir)

def ensure_nsjail_submodule():
    from subprocess import check_call

    check_call(
        ['git', 'submodule', 'update', '--init', 'nsjail/'],
        cwd=source_dir
    )
    check_call(
        ['git', 'submodule', 'update', '--init', 'kafel/'],
        cwd=source_dir / 'nsjail'
    )

def ensure_nsjail_image():
    ensure_nsjail_submodule()

    docker_compose().up(
        no_start=True,
        always_recreate_deps=True,
    ).call('nsjail')


def service_relocate_build_path(service, base_dir):
    if 'build' in service:
        if not isinstance(service['build'], str):
            raise NotImplementedError
        service['build'] = str(base_dir / service['build'])

def service_relocate_volumes_path(service, base_dir):
    volumes = service.get('volumes', [])
    for idx, volume in enumerate(volumes):
        if not isinstance(volume, str):
            raise NotImplementedError
        parts = volume.split(':')
        if len(parts) not in [1, 2, 3]:
            raise NotImplementedError
        if len(parts) == 1:
            continue
        if len(parts[0]) <= 0:
            raise NotImplementedError
        if parts[0][0] != '.':
            continue
        parts[0] = str(base_dir / parts[0])
        volume = ':'.join(parts)
        volumes[idx] = volume

def service_relocate_paths(service, base_dir):
    service_relocate_build_path(service, base_dir)
    service_relocate_volumes_path(service, base_dir)

def make_service_from_task_dir(path):
    task = path.name

    config = get_task_config_from_name(task)
    if 'compose' not in config:
        return None

    compose = get_task_config_from_name(task)['compose']
    task_ports = get_tasks_config()['ports'][task]
    ports = compose['ports']
    service = deepcopy(compose['service'])
    host = get_config()['host']

    assert len(task_ports) == len(ports)
    ports = [
        f'{host}:{task_port}:{port}'
        for task_port, port in zip(task_ports, ports)
    ]

    if 'ports' not in service:
        service['ports'] = []
    service['ports'] += ports

    service_relocate_paths(service, get_task_dir(task))

    return service

class Cannot_Start_Docker_Exception(Exception):
    pass

def is_docker_running():
    from subprocess import call, DEVNULL

    ret = call(['docker', 'info'], stdout=DEVNULL, stderr=DEVNULL)
    assert ret in [0, 1]
    return ret == 0

def ensure_docker_is_running():
    from subprocess import check_call

    if is_docker_running():
        return

    click.confirm(
        '\n'.join([
            "Docker daemon isn't running. Do you want to start it?",
            '(Polkit might ask you for password)',
            '`systemctl start docker`',
        ]),
        default=True,
        abort=True,
        err=True,
    )

    check_call(['systemctl', 'start', 'docker'])

def compose_yml_filename():
    return source_dir / '.generated/docker-compose.yml'

def create_compose_yml(filename):
    compose = deepcopy(get_config()['compose'])
    if 'services' not in compose:
        compose['services'] = {}
    services = compose['services']

    for service in services.values():
        service_relocate_paths(service, source_dir)

    for path in (source_dir / 'tasks').iterdir():
        if not is_task_dir(path):
            continue
        name = path.name
        service = make_service_from_task_dir(path)
        if service is not None:
            services[name] = service

    write_yml(compose, filename)

def ensure_compose_yml():
    yml = compose_yml_filename()
    ensure_path_parents(yml)
    create_compose_yml(yml)

@functools.lru_cache(maxsize=None)
def docker_compose():
    from docker_composer import DockerCompose

    ensure_compose_yml()
    file = [str(compose_yml_filename())]

    ensure_docker_is_running()
    return DockerCompose(file=file, project_name='ctf')


def dockerfile_has_public_target(dockerfile):
    import re

    return bool(re.search(r'(A|a)(S|s)\s+public(\s|\n|$)', dockerfile))

def tar_filter(tarinfo):
    tarinfo.uid = tarinfo.gid = 0
    tarinfo.uname = tarinfo.gname = ''
    return tarinfo

def make_task_public(task):
    from shutil import rmtree
    from subprocess import check_call, CalledProcessError
    import tarfile

    task_dir = get_task_dir(task)
    public_dir = task_dir / 'public'
    output_archive = task_dir / f'.generated/{task}.tar.gz'
    dockerfile = task_dir / 'Dockerfile'

    if output_archive.exists():
        output_archive.rename(output_archive.with_name(f'{task}.tar.gz.backup'))

    ensure_path_parents(output_archive)
    ar = tarfile.open(output_archive, 'x:gz')
    empty = True
    def ar_add_dir(path):
        nonlocal empty
        for file in path.iterdir():
            empty = False
            ar.add(file.resolve(), f'{task}/{file.name}', filter=tar_filter)
    if public_dir.exists():
        ar_add_dir(public_dir)
    if dockerfile.exists() and dockerfile_has_public_target(dockerfile.read_text()):
        dest = task_dir / '.generated/public'
        if dest.exists():
            rmtree(dest)

        tag = f'ctf_{task}_generated_public'
        check_call([
            'docker', 'build', task_dir,
            '--tag', tag,
            '--target', 'public',
            '--output', f'type=local,dest={dest}',
        ])
        # Seems like docker isn't creating an image (probably because of
        # --output).
        #  try:
        #      check_call(['docker', 'rmi', tag])
        #  except CalledProcessError as e:
        #      raise RuntimeError(f"Couldn't remove docker image '{tag}'.") from e

        ar_add_dir(dest)

    ar.close()

    if empty:
        click.echo("There aren't any public files.")
    else:
        click.echo(str(output_archive))

#  def open_port(port):
#      from subprocess import call, check_call
#
#      def args(mode):
#          return [
#              'iptables',
#              mode, 'public',
#              '--protocol', 'tcp',
#              '--dport', str(port),
#              '--jump', 'ACCEPT',
#          ]
#
#      if call(args('-C')) != 0:
#          check_call(args('-A'))

def _services_up_common(services):
    docker_compose().up(
        detach=True,
        build=True,
        always_recreate_deps=True,
    ).call(*services)

    # Docker opens ports automatically. :O
    #  if production:
    #      def open_ports_for_service(name, port_list):
    #          if services == [] or name in services:
    #              for port in port_list:
    #                  open_port(port)
    #      config = get_tasks_config()
    #      for name, port_list in config['ports'].items():
    #          open_ports_for_service(name, port_list)
    #      open_ports_for_service('nginx', [80, 443])

def get_dependant_services():
    if production:
        return ['ctfd', 'ctfd-db', 'ctfd-cache']
    else:
        return ['ctfd-db', 'ctfd-cache']

def check_dependant_services(services, *, operation):
    dependant_services = sorted(set(get_dependant_services()) & set(services))
    if len(dependant_services) > 0:
        servs = oxford_comma_join(dependant_services)
        click.confirm(
            f'Are you sure you want to {operation} {servs}?',
            default=False,
            abort=True,
            err=True,
        )

def services_up(services, **kwargs):
    assert len(services) > 0, services

    check_dependant_services(services, operation='up')

    if 'ctfd' in services or 'nginx' in services:
        ensure_ctfd_submodule()

    # Check if one of services needs nsjail.
    for service in services:
        dockerfile = get_task_dir(service) / 'Dockerfile'
        if not dockerfile.exists():
            continue
        if b'ctf_nsjail' in dockerfile.read_bytes():
            ensure_nsjail_image()
            break

    _services_up_common(services, **kwargs)

def services_up_ctfd_and_tasks(**kwargs):
    ensure_ctfd_submodule()
    ensure_nsjail_image()

    services = get_tasks_config()['ctfd']
    if production:
        services += ['nginx']
    else:
        services += ['ctfd']
    _services_up_common(services, **kwargs)


def _services_stop_common(services):
    docker_compose().stop().call(*services)

def services_stop(services, **kwargs):
    assert len(services) > 0, services

    check_dependant_services(services, operation='stop')

    services = list(services)
    if 'nginx' in services:
        services.append('ctfd')
    if 'ctfd' in services:
        services.append('ctfd-db')
        services.append('ctfd-cache')

    _services_stop_common(services, **kwargs)

def services_stop_all(**kwargs):
    _services_stop_common([], **kwargs)


def _services_logs_common(services, follow=False, tail_all=False):
    docker_compose().logs(
        timestamps=True,
        follow=follow,
        **({'tail': 'all'} if tail_all else {}),
    ).call(*services)

def services_logs(services, **kwargs):
    assert len(services) > 0, services

    _services_logs_common(services, **kwargs)

def services_logs_all(**kwargs):
    _services_logs_common([], **kwargs)


@click.group()
@click.option(
    '--prod/--local',
    envvar='CTF_PROD',
    default=False,
    hidden=True,
)
def cli(*, prod):
    global production
    production = prod

@cli.command()
# TODO: Service name shell completions.
@click.argument('service', nargs=-1)
def up(*, service, **kwargs):
    services = service

    if len(services) > 0:
        services_up(services, **kwargs)
    else:
        if not production:
            click.confirm(
                'Are you sure you want to up all services?',
                default=False,
                abort=True,
                err=True,
            )
        services_up_ctfd_and_tasks(**kwargs)

@cli.command()
@click.argument('service', nargs=-1)
def stop(*, service, **kwargs):
    services = service

    if len(services) > 0:
        services_stop(services, **kwargs)
    else:
        services_stop_all(**kwargs)

@cli.command()
@click.argument('service', nargs=-1)
@click.option('--follow/--no-follow', default=False)
@click.option('--all/--no-all', 'tail_all', default=False)
def logs(*, service, **kwargs):
    services = service

    if len(services) > 0:
        services_logs(services, **kwargs)
    else:
        services_logs_all(**kwargs)

@cli.command()
def ps():
    docker_compose().ps().call()

@cli.command()
def prune():
    if production:
        click.confirm(
            'Are you sure you want to prune production?',
            default=False,
            abort=True,
            err=True,
        )
        click.confirm(
            'Did you made backup?',
            default=False,
            abort=True,
            err=True,
        )
        click.confirm(
            'Are you *absolutely* sure you want to prune production?',
            default=False,
            abort=True,
            err=True,
        )

    docker_compose().down(
        remove_orphans=True,
        volumes=True,
        rmi='all',
    ).call()

def make_public_task_cb(ctx, param, value):
    if value is not None:
        return value
    if is_task_dir(Path.cwd()):
        return Path.cwd().name
    raise click.MissingParameter()

@cli.command()
@click.argument('task', required=False, callback=make_public_task_cb)
@click.pass_context
def make_public(ctx, *, task):
    make_task_public(task)

@cli.command(
    'docker-compose',
    add_help_option=False,
    context_settings={'ignore_unknown_options': True},
)
@click.argument('args', nargs=-1)
def cli_docker_compose(*, args):
    docker_compose().call(*args)


if __name__ == '__main__':
    single_instance = SingleInstance()

    loglevel = os.environ.get('CTF_LOGLEVEL', 'WARNING')
    logging.basicConfig(level=loglevel)
    try:
        from loguru import logger
        logger.remove(0)
        logger.add(sys.stderr, level=loglevel)
    except ImportError:
        pass

    cli()

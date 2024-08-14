import re
import subprocess
from pprint import pprint
from copr.v3 import Client
from productmd.common import parse_nvra

# The packages that we build in Copr:
PACKAGES = {
    'python3.11-decorator': (8, 9),
    'python3.11-dnf': (8, 9),
    'python3.11-gpg': (8,),
    'python3.11-gssapi': (8, 9),
    'python3.11-libcomps': (8, 9),
    'python3.11-libdnf': (8, 9),
    'python3.11-requests-gssapi': (8, 9),
}


def podman(*args, **kwargs):
    args = ('podman',) + args
    return subprocess.check_output(args, **kwargs)


def podman_run(container, *args, **kwargs):
    """ Run a command in a throwaway container """
    name = f'copr-test-{container}'
    args = ('run', '-it', '--name', name, container) + args
    return podman(*args, **kwargs)


def find_rhel_nvr(container, rpm):
    # XXX this will only work for packages that are not in EPEL. Need to
    # install EPEL... see the comment below about doing this all at once.
    rpm_qv = podman_run(container, 'dnf', 'repoquery', '-q', '-s', rpm, text=True).strip()
    return parse_nvra(rpm_qv)


def rhel_package_name(copr_package):
    return re.sub('^python3.11-', 'python3-', copr_package)


def find_copr_nvr(client, copr_package, os_version):
    builds = client.build_proxy.get_list('ktdreyer', 'python3.11', copr_package, status='succeeded')
    chroot = f'epel-{os_version}-x86_64'
    # Trusting that "builds" is ordered properly here, that the first results
    # are the newest...
    for build in builds:
        if chroot in build.chroots:
            break
    data = client.build_proxy.get_built_packages(build.id)
    packages = data[chroot]['packages']
    nvr = packages[0].copy()
    nvr['name'] = copr_package
    return nvr


def verrel_equal(rhel_nvr, copr_nvr):
    print('RHEL: {name}-{version}-{release}'.format(**rhel_nvr))
    print('Copr: {name}-{version}-{release}'.format(**copr_nvr))
    return bool(rhel_nvr['version'] == copr_nvr['version'] and rhel_nvr['release'] != copr_nvr['release'])


def update_copr(copr_package, rhel_nvr, os_version):
    version = rhel_nvr['version']
    release = rhel_nvr['release']
    chroot = f'epel-{os_version}-x86_64'
    print(f'TODO: updating {copr_package} to {version}-{release} for {chroot}')


def main():
    client = Client.create_from_config_file()

    # TODO: assemble the full list of RHEL packages and run repoquery on all
    # of them at once, rather than trying to query them one by one.

    for copr_package, os_versions in PACKAGES.items():
        for os_version in os_versions:
            container = f'ubi{os_version}'
            rhel_package = rhel_package_name(copr_package)  # eg "python3-libdnf"
            rhel_nvr = find_rhel_nvr(container, rhel_package)
            copr_nvr = find_copr_nvr(client, copr_package, os_version)
            if verrel_equal(rhel_nvr, copr_nvr):
                update_copr(copr_package, rhel_nvr, os_version)

    # podman('rm', '-i', 'copr-test-ubi8', 'copr-test-ubi9')


if __name__ == '__main__':
    main()

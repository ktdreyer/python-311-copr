import re
import subprocess
from pprint import pprint
from copr.v3 import Client
from productmd.common import parse_nvra

# The packages that we build in Copr:
PACKAGES = {
    '8': [
        'python3.11-decorator',
        'python3.11-dnf',
        'python3.11-gpg',  # I used the version from EPEL 9
        'python3.11-gssapi',
        'python3.11-libcomps',
        'python3.11-libdnf',
        'python3.11-requests-gssapi',
    ],
    '9': [
        'python3.11-decorator',
        'python3.11-dnf',
        'python3.11-gssapi',
        'python3.11-libcomps',
        'python3.11-libdnf',
        'python3.11-requests-gssapi',
    ],
}


def podman(*args, **kwargs):
    args = ('podman',) + args
    print('+ ' + ' '.join(args))
    return subprocess.check_output(args, **kwargs)


def podman_run(container, *args, **kwargs):
    """ Run a command in a throwaway container """
    name = f'copr-test-{container}'
    args = ('run', '-itd', '--replace', '--name', name, container) + args
    return podman(*args, **kwargs)


def find_rhel_nvrs(os_version, names):
    """
    Find NVRs outside Copr (UBI repos and EPEL)
    """
    base_image = f'ubi{os_version}'
    container = f'copr-test-{base_image}'
    podman_run(base_image, 'sleep', 'infinity')
    epel = f'https://dl.fedoraproject.org/pub/epel/epel-release-latest-{os_version}.noarch.rpm'
    podman('exec', container, 'dnf', '-y', 'install', epel)
    output = podman('exec', container, 'dnf', 'repoquery', '-q', *names, text=True).strip()
    rpms = output.splitlines()
    nvrs = [parse_nvra(rpm) for rpm in rpms]
    missing = []
    for name in names:
        found = bool([nvr['name'] for nvr in nvrs if nvr['name'] == name])
        if not found:
            missing.append(name)
    for name in missing:
        print(f'missing {name} in {container} repoquery')
    if missing:
        raise ValueError(missing)
    return nvrs


def rhel_package_names(copr_packages):
    return [re.sub('^python3.11-', 'python3-', p) for p in copr_packages]


def find_copr_nvrs(client, os_version, copr_packages):
    chroot = f'epel-{os_version}-x86_64'
    nvrs = []
    for copr_package in copr_packages:
        builds = client.build_proxy.get_list('ktdreyer', 'python3.11', copr_package, status='succeeded')
        if not builds:
            raise ValueError(copr_package)
        # Trusting that "builds" is ordered properly here, that the first results
        # are the newest...
        for build in builds:
            if chroot in build.chroots:
                break
        assert chroot in build.chroots
        data = client.build_proxy.get_built_packages(build.id)
        packages = data[chroot]['packages']
        nvr = packages[0].copy()
        nvr['name'] = copr_package
        nvrs.append(nvr)
    return nvrs


def verrel_equal(rhel_nvr, copr_nvr):
    # print('RHEL: {name}-{version}-{release}'.format(**rhel_nvr))
    # print('Copr: {name}-{version}-{release}'.format(**copr_nvr))
    return bool(rhel_nvr['version'] == copr_nvr['version'] and rhel_nvr['release'] != copr_nvr['release'])


def update_copr(copr_package, rhel_nvr, os_version):
    version = rhel_nvr['version']
    release = rhel_nvr['release']
    chroot = f'epel-{os_version}-x86_64'
    print(f'TODO: updating {copr_package} to {version}-{release} for {chroot}')


def main():
    client = Client.create_from_config_file()

    for os_version, copr_packages in PACKAGES.items():
        rhel_packages = rhel_package_names(copr_packages)
        rhel_nvrs = find_rhel_nvrs(os_version, rhel_packages)
        copr_nvrs = find_copr_nvrs(client, os_version, copr_packages)
        for rhel_nvr, copr_nvr in zip(rhel_nvrs, copr_nvrs):
            if verrel_equal(rhel_nvr, copr_nvr):
                update_copr(copr_nvr, rhel_nvr, os_version)

    # podman('rm', '-i', 'copr-test-ubi8', 'copr-test-ubi9')


if __name__ == '__main__':
    main()

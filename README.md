[![test package installs](https://github.com/ktdreyer/python-311-copr/actions/workflows/tests.yml/badge.svg)](https://github.com/ktdreyer/python-311-copr/actions/workflows/tests.yml)

Extra libraries for Python 3.11 on RHEL 8 and 9. Requires EPEL.

https://copr.fedorainfracloud.org/coprs/ktdreyer/python3.11/

Useful for [errata-tool-ansible](https://github.com/ktdreyer/errata-tool-ansible).

## Installation Instructions

```
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-$(rpm -E '%{rhel}').noarch.rpm
dnf copr enable -y ktdreyer/python3.11
```

Then install `python3.11` packages, for example:

```
yum -y install python3.11-requests-gssapi
# OR
yum -y install python3.11-dnf
```

## Rebuilding locally:

To build a package from dist-git, using mock:

```
fedpkg --release epel8 mockbuild --root rhel+epel-8-x86_64 -- --addrepo=https://download.copr.fedorainfracloud.org/results/ktdreyer/python3.11/epel-8-x86_64/

fedpkg --release epel9 mockbuild --root rhel+epel-9-x86_64 -- --addrepo=https://download.copr.fedorainfracloud.org/results/ktdreyer/python3.11/epel-9-x86_64/

```

## Bugs

I've copied and and heavily modified packages from RHEL for this. When the RHEL maintainers ship an update to the underlying libraries (eg rpm-lib), I must merge RHEL's changes in and rebuild.

These packages also depend on `python3.11-rpm` from EPEL where we have the same convention. For example, https://bugzilla.redhat.com/show_bug.cgi?id=2265373

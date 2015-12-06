# Created by pyp2rpm-1.1.2
%global pypi_name feaders
%global server_name %{pypi_name}-server
%global service_user %{pypi_name}

Name:           python-%{pypi_name}
Version:        0.2.0
Release:        1%{?dist}
Summary:        Fedora headers searcher

License:        MIT
URL:            https://codeload.github.com/shaded-enmity/feaders
Source0:        %{url}/tar.gz/%{version}
BuildArch:      noarch
 
BuildRequires:  python2-devel
BuildRequires:  systemd
 
Requires:       librepo
Requires:       python-requests
Requires:       python-flask
Requires(pre): /usr/sbin/useradd, /usr/bin/getent

%pre
/usr/bin/getent passwd %{service_user} || /usr/sbin/useradd -r -d /usr/bin -s /sbin/nologin %{service_user}

%description
Package provides CLI for fast resolution of included files
in project path, and Server part that can be used to significantly
speed up the search via querying the repository database directly.

%prep
%setup -q -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%{__python2} setup.py build

%install
%{__python2} setup.py install --skip-build --root %{buildroot}
mkdir -p %{buildroot}%{_sysconfdir}/
mkdir -p %{buildroot}%{_unitdir}/
mkdir -p %{buildroot}%{_datadir}/feaders/
cp -R server/* %{buildroot}%{_datadir}/feaders/
cp feaders-server.service %{buildroot}%{_unitdir}/
cp feaders.env %{buildroot}%{_sysconfdir}/
cp feaders.auth %{buildroot}%{_sysconfdir}/

%files
%doc 
%attr(600, feaders, feaders) %{_sysconfdir}/feaders.env
%attr(600, feaders, feaders) %{_sysconfdir}/feaders.auth
%config %{_sysconfdir}/feaders.env
%config %{_sysconfdir}/feaders.auth
%{_unitdir}/feaders-server.service
%{_bindir}/feaders
%{_bindir}/feaders-server
%{_datadir}/feaders
%{python2_sitelib}/feader
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%changelog
* Sat Dec 05 2015 Pavel Odvody - 0.2.0-1
- Initial package.

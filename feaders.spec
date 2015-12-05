# Created by pyp2rpm-1.1.2
%global pypi_name feaders
%global server_name %{pypi_name}-server
%global service_user %{pypi_name}

Name:           python-%{pypi_name}
Version:        0.1.0
Release:        1%{?dist}
Summary:        Fedora headers searcher

License:        MIT
URL:            http://github.com/shaded-enmity/feaders
Source0:        %{url}/releases/%{pypi_name}/%{version}.tgz
BuildArch:      noarch
 
BuildRequires:  python2-devel
 
Requires:       python-requests
Requires:       python-flask
Requires(pre): /usr/sbin/useradd, /usr/bin/getent
Requires(postun): /usr/sbin/userdel

%pre
/usr/bin/getent group %{service_user} || /usr/sbin/groupadd -r %{service_user}
/usr/bin/getent passwd %{service_user} || /usr/sbin/useradd -r -d /usr/bin -s /sbin/nologin %{service_user}

%description
Packa provides CLI for fast resolution of included files
in project path, and Server part that can be used to significantly
speed up the search via querying the repository database directly.

%prep
%setup -q -n %{pypi_name}-%{version}
# Remove bundled egg-info
rm -rf %{pypi_name}.egg-info

%build
%{__python2} setup.py build
cp feaders-server.service  %{_unitdir}/

%install
%{__python2} setup.py install --skip-build --root %{buildroot}

%files
%doc 
%{_unitdir}/feaders-server.service
%{_bindir}/feaders
%{_bindir}/feaders-server
%{python2_sitelib}/%{pypi_name}
%{python2_sitelib}/%{pypi_name}-%{version}-py?.?.egg-info

%changelog
* Sat Dec 05 2015 Pavel Odvody - 0.1.0-1
- Initial package.

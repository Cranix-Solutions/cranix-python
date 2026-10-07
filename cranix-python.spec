#
# spec file for package python-cranix
#
# Copyright (c) 2026 Peter Varkoly, Nuernberg, Germany.
#
# All modifications and additions to the file contributed by third parties
# remain the property of their copyright owners, unless otherwise agreed
# upon. The license for that file, and modifications and additions to the
# file, is the same license as for the pristine package itself.
#

Name:           python-cranix
Version:        ##VERSION##
Release:        0
Summary:        Common Python modules and native REST API client for CRANIX
License:        CC-BY-NC-ND-4.0
URL:            https://github.com/Cranix-Solutions/cranix-python
Source:         cranix-python-%{version}.tar.xz
BuildRequires:  python-rpm-macros
BuildRequires:  %{python_module pip}
BuildRequires:  %{python_module setuptools}
BuildRequires:  %{python_module wheel}
BuildRequires:  fdupes
BuildArch:      noarch
%python_subpackages

%description
Common Python modules and a native REST API client for the CRANIX.
This package replaces the shell based crx_api helpers for Python code.

%prep
%autosetup -p1 -n cranix-python-%{version}

%build
%pyproject_wheel

%install
%pyproject_install
%python_expand %fdupes %{buildroot}%{$python_sitelib}

%files %{python_files}
%license LICENSE
%doc README.md
%{python_sitelib}/cranix
%{python_sitelib}/cranix-%{version}.dist-info

%changelog

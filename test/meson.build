# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

project(
  'example-project',
  ['c', 'cpp'],
  version: '1.0.0',
  license: 'MPL-2.0',
  default_options: [
    'c_std=c11',
    'cpp_std=c++20',
    'warning_level=3',
    'buildtype=debugoptimized',
  ],
  meson_version: '>=1.2.0',
)

# Basic project metadata and build options
proj_name = meson.project_name()
proj_version = meson.project_version()
proj_ver_arr = proj_version.split('.')

build_mach = meson.current_build_machine()
host_mach = meson.current_host_machine()

opt_a = get_option('opt_a')
opt_b = get_option('opt_b')
opt_debug = get_option('debug')
opt_test = get_option('test', fallback: false)

# Compilers and tools
c_comp = meson.get_compiler('c')
cpp_comp = meson.get_compiler('cpp')

python3_prg = find_program('python3', required: true)
pkgconf = find_program('pkg-config', required: false)

# Generic flags/deps
global_args = []
global_deps = []

# OS / compiler feature checks
has_posix = c_comp.has_header('unistd.h')
has_threads = c_comp.has_function('pthread_create', dependencies: dependency('threads', required: false))
has_std_filesystem = cpp_comp.has_header('filesystem') and cpp_comp.has_argument('-std=c++17', required: false)

if has_std_filesystem
  global_args += ['-DUSE_STD_FILESYSTEM']
endif

if host_mach.system() == 'windows'
  global_args += ['-DPLATFORM_WINDOWS']
elif host_mach.system() == 'darwin'
  global_args += ['-DPLATFORM_MACOS']
else
  global_args += ['-DPLATFORM_UNIX']
endif

# Example of a feature option w/ feature option type
feature_opt = get_option('feature_x')
feature_enabled = feature_opt.allowed() and feature_opt.enabled()

# Subproject with forwarded options and variable access
base_sub = subproject(
  'base-subproject',
  default_options: [
    f'opt_a=@opt_a@',
    f'opt_b=@opt_b@',
  ],
)

base_dep = base_sub.get_variable('base_dep')
config_helper_py = base_sub.get_variable('config_helper_py')
base_config_h = base_sub.get_variable('config_h')

global_deps += [base_dep]

# Another subproject providing a dependency, with conditional usage
extra_sub = subproject(
  'extra-lib',
  default_options: ['warning_level=2'],
)
extra_dep = extra_sub.get_variable('extra_dep')
global_deps += [extra_dep]
global_args += ['-DHAVE_EXTRA_LIB=1']

# Read a simple key:value metadata file
fs = import('fs')
mod_info = {}

foreach l : fs.read('module.info').strip().split('\n')
  if l == ''
    continue
  endif
  s = l.split(':')
  k = s[0]
  v = s[1]
  foreach i : range(2, s.length())
    v += ':' + s[i]
  endforeach
  mod_info += {k: v.strip()}
endforeach

# Generate a small header using configure_file (simple mode)
conf_data = configuration_data()
conf_data.set('PROJ_NAME', proj_name)
conf_data.set('PROJ_VERSION', proj_version)
conf_data.set('HAS_POSIX', has_posix ? 1 : 0)

simple_conf_h = configure_file(
  input: 'simple-config.h.in',
  output: 'simple-config.h',
  configuration: conf_data,
)

# Optional dependency with a compile/run test
opt_dep = dependency('optional-lib', required: false)

if opt_dep.found()
  t = cpp_comp.run(
    '''
    #include <cstdint>
    #include <type_traits>
    int main() {
      using int_t = int32_t;
      if constexpr (std::is_same_v<int_t, int>) return 0;
      return 1;
    }
    ''',
    dependencies: opt_dep,
  )
  assert(t.compiled() and t.returncode() == 0)
  global_args += ['-DHAVE_OPTIONAL_LIB=1']
  global_deps += [opt_dep]
endif

# Example of a dependency with fallback
fmt_dep = dependency(
  'fmt',
  required: false,
  fallback: ['fmt-subproject', 'fmt_dep'],
  version: '>=9.0.0',
)
if fmt_dep.found()
  global_deps += [fmt_dep]
  global_args += ['-DUSE_FMT']
endif

# Construct config map for more complex config generation
cfg = {
  'MOD_MAINTAINER': mod_info.get('Maintainer', ''),
  'MOD_NAME': mod_info.get('Module', ''),
  'MOD_URL': mod_info.get('URL', ''),
  'MOD_VERSION': proj_version,
  'MOD_VER_MAJOR': proj_ver_arr[0].to_int(),
  'MOD_VER_MINOR': proj_ver_arr[1].to_int(),
  'MOD_VER_PATCH': proj_ver_arr[2].to_int(),
  'HAS_POSIX': has_posix ? 1 : 0,
  'HAS_THREADS': has_threads ? 1 : 0,
}

if feature_enabled
  cfg += {'FEATURE_X': 1}
  global_args += ['-DFEATURE_X_ENABLED']
endif

# Build string config blob
config_str = ''
foreach k, v : cfg
  config_str += f'@k@=@v@\n'
endforeach

# Scripted configure_file usage
project_conf_h = configure_file(
  input: 'config.h.in',
  output: 'project-config.hh',
  command: [
    python3_prg,
    config_helper_py,
    base_config_h,
    '@INPUT@',
    '@OUTPUT@',
    config_str,
  ],
)

# Generated source file example
gen_src = custom_target(
  'generated-source',
  input: 'gen-input.txt',
  output: 'generated.cc',
  command: [python3_prg, files('scripts/gen_src.py'), '@INPUT@', '@OUTPUT@'],
)

# Include dirs
inc_root = include_directories('.')
inc_gen = include_directories(meson.current_build_dir())

# Main library built from mixed sources
lib_src = files(
  'src/main.cc',
  'src/util.cc',
)

lib = library(
  'example',
  [lib_src, gen_src],
  include_directories: [inc_root, inc_gen],
  dependencies: global_deps,
  cpp_args: global_args,
  install: true,
  install_dir: get_option('libdir'),
)

# A small helper library (object library usage)
helper_obj = object_library(
  'helper-obj',
  'src/helper.c',
  include_directories: inc_root,
)

helper_lib = static_library(
  'helper',
  helper_obj,
  include_directories: inc_root,
  install: true,
)

# Main executable
exe = executable(
  'example-bin',
  'src/main-exe.cc',
  include_directories: [inc_root, inc_gen],
  dependencies: global_deps,
  link_with: [lib, helper_lib],
  cpp_args: global_args,
  install: true,
  install_dir: get_option('bindir'),
)

# Alias target example
alias_target('all-examples', exe)

# Install extra data files
install_data(
  'module.info',
  install_dir: join_paths(get_option('datadir'), proj_name),
)

# Install configuration header as part of public interface
install_headers(
  [project_conf_h, simple_conf_h],
  subdir: proj_name,
)

# Declare a dependency for users of this project
project_dep = declare_dependency(
  include_directories: [inc_root, inc_gen],
  dependencies: global_deps,
  link_with: [lib],
  compile_args: global_args,
)

# Export dependency in a pkg-config file
pkgconf_data = configuration_data()
pkgconf_data.set('prefix', get_option('prefix'))
pkgconf_data.set('libdir', get_option('libdir'))
pkgconf_data.set('includedir', get_option('includedir'))
pkgconf_data.set('proj_name', proj_name)
pkgconf_data.set('proj_version', proj_version)

pc = configure_file(
  input: 'example.pc.in',
  output: f'@proj_name@.pc',
  configuration: pkgconf_data,
  install: true,
  install_dir: join_paths(get_option('libdir'), 'pkgconfig'),
)

# Meson summary
summary(
  {
    'Project name': proj_name,
    'Version': proj_version,
    'Host': host_mach.system(),
    'Optional lib': opt_dep.found(),
    'fmt': fmt_dep.found(),
    'Feature X': feature_enabled,
    'POSIX': has_posix,
    'Threads': has_threads,
  },
  section: 'Configuration',
  bool_yn: true,
)

# Tests
if opt_test
  subdir('tests')
endif

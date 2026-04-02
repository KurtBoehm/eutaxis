# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

project(
  'example-project',
  'c',
  'cpp',
  version: '1.0.0',
  default_options: ['cpp_std=c++20', 'warning_level=3'],
  license: 'MPL-2.0',
)

mod_version = meson.project_version()
mod_version_split = mod_version.split('.')

cpp_compiler = meson.get_compiler('cpp')

args = []
deps = []

# Example of forwarding options to a subproject
opt_a = get_option('opt_a')
opt_b = get_option('opt_b')
base_sub = subproject(
  'base-subproject',
  default_options: [
    f'opt_a=@opt_a@',
    f'opt_b=@opt_b@',
  ],
)
base_dep = base_sub.get_variable('base_dep')
deps += [base_dep]

# Read a simple key:value metadata file
fs = import('fs')
mod_info = {}
foreach l : fs.read('module.info').strip().split('\n')
  if l == ''
    continue
  endif
  split = l.split(':')
  key = split[0]
  value = split[1]
  foreach i : range(2, split.length())
    value += ':' + split[i]
  endforeach
  mod_info += {key: value.strip()}
endforeach

python3_prg = find_program('python3')

cfg = {
  'MOD_MAINTAINER': mod_info.get('Maintainer', ''),
  'MOD_NAME': mod_info.get('Module', ''),
  'MOD_URL': mod_info.get('URL', ''),
  'MOD_VERSION': mod_version,
  'MOD_VERSION_MAJOR': mod_version_split[0].to_int(),
  'MOD_VERSION_MINOR': mod_version_split[1].to_int(),
  'MOD_VERSION_PATCH': mod_version_split[2].to_int(),
}

# Optional dependency with a small compile test
opt_dep = dependency('optional-lib', required: false)
if opt_dep.found()
  test_res = cpp_compiler.run(
    '''
    #include <cstdint>
    #include <type_traits>
    int main() {
      using int_t = int32_t;
      if constexpr (std::is_same_v<int_t, int>) return 0;
      return 1;
    }
    ''',
    dependencies: [opt_dep],
  )
  assert(test_res.compiled() and test_res.returncode() == 0)
  cfg += {'OPTIONAL_LIB_INT32_TYPE': 'int'}
  args += ['-DHAVE_OPTIONAL_LIB=1']
  deps += [opt_dep]
endif

# Another subproject providing a dependency
extra_dep = subproject('extra-lib').get_variable('extra_dep')
deps += [extra_dep]
args += ['-DHAVE_EXTRA_LIB=1']

config_helper_py = base_sub.get_variable('config_helper_py')
base_config_h = base_sub.get_variable('config_h')

config_str = ''
foreach key, value : cfg
  config_str += f'@key@=@value@\n'
endforeach

config_h = configure_file(
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

project_dep = declare_dependency(
  include_directories: include_directories('.'),
  dependencies: deps,
  compile_args: args,
)

if get_option('test')
  subdir('tests')
endif

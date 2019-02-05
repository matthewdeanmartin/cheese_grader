# coding=utf-8
"""
Build tasks
"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import glob
import json
import os
import subprocess
import sys

from pynt import task
from pyntcontrib import execute, safe_cd
from semantic_version import Version

PROJECT_NAME = "cheese_grader"
SRC = '.'
# for multitargeting
PYTHON = "python"
IS_DJANGO = False
IS_TRAVIS = 'TRAVIS' in os.environ
if IS_TRAVIS:
    PIPENV = ""
else:
    PIPENV = "pipenv run"
GEM_FURY = ""

CURRENT_HASH = None

MAC_LIBS = ":"

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from build_utils import check_is_aws, skip_if_no_change, execute_with_environment, get_versions, execute_get_text, \
    run_gitleaks, timed

# try to stop the "you are already in a pipenv shell noise.
os.environ["PIPENV_VERBOSITY"] = "-1"

@task()
@skip_if_no_change("git_leaks")
@timed()
def git_leaks():
    run_gitleaks()


@task()
@skip_if_no_change("git_secrets")
@timed()
def git_secrets():
    """
    Install git secrets if possible.
    """

    if check_is_aws():
        # no easy way to install git secrets on ubuntu.
        return
    if IS_TRAVIS:
        # nothing is edited on travis
        return
    try:
        commands = ["git secrets --install", "git secrets --register-aws"]
        for command in commands:
            cp = subprocess.run(command.split(" "),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                shell=False, check=True)
            for stream in [cp.stdout, cp.stderr]:
                if stream:
                    for line in stream.decode().split("\n"):
                        print("*" + line)
    except subprocess.CalledProcessError as cpe:
        print(cpe)
        installed = False
        for stream in [cpe.stdout, cpe.stderr]:
            if stream:
                for line in stream.decode().split("\n"):
                    print("-" + line)
                    if "commit-msg already exists" in line:
                        print("git secrets installed.")
                        installed = True
                        break
        if not installed:
            raise
    execute(*("git secrets --scan".strip().split(" ")))


@task()
@timed()
def clean():
    """
    Delete all outputs. Blank until I think of a better way to do this.
    """
    return


@task()
@skip_if_no_change("formatting")
@timed()
def formatting():
    with safe_cd(SRC):
        if sys.version_info < (3, 6):
            print("Black doesn't work on python 2")
            return
        command = "{0} black {1}".format(PIPENV, PROJECT_NAME).strip()
        print(command)
        result = execute_get_text(command)
        assert result
        changed = []
        for line in result.split("\n"):
            if "reformatted " in line:
                file = line[len("reformatted "):].strip()
                changed.append(file)
        for change in changed:
            command = "git add {0}".format(change)
            print(command)
            execute(*(command.split(" ")))


@task()
@skip_if_no_change("compile_py")
@timed()
def compile_py():
    """
    Catch on the worst syntax errors
    """
    with safe_cd(SRC):
        execute(PYTHON, "-m", "compileall", PROJECT_NAME)


@task(formatting, compile_py)
@skip_if_no_change("prospector")
@timed()
def prospector():
    """
    Catch a few things with a non-strict propector run
    """
    with safe_cd(SRC):
        command = "{0} prospector {1} --profile {1}_style --pylint-config-file=pylintrc.ini --profile-path=.prospector".format(
            PIPENV, PROJECT_NAME).strip().replace("  ", " ")
        print(command)
        execute(*(command
                  .split(" ")))


@task()
@skip_if_no_change("detect_secrets")
@timed()
def detect_secrets():
    """
    Call detect-secrets tool
    """
    # use
    # blah blah = "foo"     # pragma: whitelist secret
    # to ignore a false posites
    errors_file = "detect-secrets-results.txt"

    print(execute_get_text("pwd"))

    command = "{0} detect-secrets --scan --base64-limit 4 --exclude .idea|.js|.min.js|.html|.xsd|" \
              "lock.json|synced_folders|.scss|Pipfile.lock|" \
              "lint.txt|{1}".format(PIPENV, errors_file).strip()
    print(command)
    bash_process = subprocess.Popen(command.split(" "),
                                    # shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
    foo = bash_process.wait()
    out, err = bash_process.communicate()  # wait

    with open(errors_file, "w+") as file_handle:
        if len(out) == 0:
            print("Warning- no output from detect secrets. Happens with git hook, but not from ordinary command line.")
            return
        file_handle.write(out.decode())

    with open(errors_file) as f:
        try:
            data = json.load(f)
        except Exception:
            print("Can't read json")
            exit(-1)
            return

    if data["results"]:
        for result in data["results"]:
            print(result)
        print("detect-secrets has discovered high entropy strings, possibly passwords?")
        exit(-1)


@task(compile_py, formatting, prospector)
@skip_if_no_change("lint")
@timed()
def lint():
    """
    Lint
    """
    with safe_cd(SRC):
        if os.path.isfile("lint.txt"):
            execute("rm", "lint.txt")

    with safe_cd(SRC):
        if IS_DJANGO:
            django_bits = "--load-plugins pylint_django "
        else:
            django_bits = ""

        # command += "{0}--rcfile=pylintrc.ini {1}".format(django_bits, PROJECT_NAME).split(" ")
        command = "{0} pylint {1} --rcfile=pylintrc.ini {2}".format(PIPENV, django_bits, PROJECT_NAME) \
            .strip() \
            .replace("  ", " ")
        print(command)
        command = command.split(" ")

        # keep out of src tree, causes extraneous change detections
        lint_output_file_name = "lint.txt"
        with open(lint_output_file_name, "w") as outfile:
            env = config_pythonpath()
            subprocess.call(command, stdout=outfile, env=env)

        fatal_errors = sum(1 for line in open(lint_output_file_name)
                           if "no-member" in line or \
                           "no-name-in-module" in line or \
                           "import-error" in line)

        if fatal_errors > 0:
            for line in open(lint_output_file_name):
                if "no-member" in line or \
                        "no-name-in-module" in line or \
                        "import-error" in line:
                    print(line)

            print("Fatal lint errors : {0}".format(fatal_errors))
            exit(-1)

        cutoff = 100
        num_lines = sum(1 for line in open(lint_output_file_name)
                        if "*************" not in line
                        and "---------------------" not in line
                        and "Your code has been rated at" not in line)
        if num_lines > cutoff:
            raise TypeError("Too many lines of lint : {0}, max {1}".format(num_lines, cutoff))


@task(lint)
@skip_if_no_change("nose_tests")
@timed()
def nose_tests():
    """
    Nose tests
    """
    # with safe_cd(SRC):
    if IS_DJANGO:
        command = "{0} manage.py test -v 2".format(PYTHON)
        # We'd expect this to be MAC or a build server.
        my_env = config_pythonpath()
        execute_with_environment(command, env=my_env)
    else:
        my_env = config_pythonpath()
        if IS_TRAVIS:
            command = "{0} -m nose {1}".format(PYTHON, "test").strip()
        else:
            command = "{0} {1} -m nose {2}".format(PIPENV, PYTHON, "test").strip()
        print(command)
        execute_with_environment(command, env=my_env)


def config_pythonpath():
    """
    Add to PYTHONPATH
    """
    if check_is_aws():
        env = "DEV"
    else:
        env = "MAC"
    my_env = {'ENV': env,
              "PIPENV_VERBOSITY": "-1"}
    for key, value in os.environ.items():
        my_env[key] = value
    my_env["PYTHONPATH"] = my_env.get("PYTHONPATH",
                                      "") + MAC_LIBS
    print(my_env["PYTHONPATH"])
    return my_env


@task()
@timed()
def coverage():
    """
    Coverage, which is a bit redundant with nose test
    """
    print("Coverage tests always re-run")
    with safe_cd(SRC):
        my_env = config_pythonpath()
        command = "{0} py.test {1} --cov={2} --cov-report html:coverage --cov-fail-under 40  --verbose".format(
            PIPENV,
            "test", PROJECT_NAME)
        execute_with_environment(command, my_env)


@task()
@skip_if_no_change("docs")
@timed()
def docs():
    """
    Docs
    """
    with safe_cd(SRC):
        with safe_cd("docs"):
            my_env = config_pythonpath()
            command = "{0} make html".format(PIPENV).strip()
            print(command)
            execute_with_environment(command, env=my_env)


@task()
@timed()
def pip_check():
    """
    Are packages ok?
    """
    execute("pip", "check")
    execute("twine", "check")
    if PIPENV and not IS_TRAVIS:
        execute("pipenv", "check")
    execute("safety", "check", "-r", "requirements_dev.txt")


@task()
@timed()
def compile_mark_down():
    """
    Convert MD to RST
    """
    # print("Not compiling README.md because moderately complex MD makes pypi rst parser puke.")
    with safe_cd(SRC):
        if IS_TRAVIS:
            command = "pandoc --from=markdown --to=rst --output=README.rst README.md".strip().split(
                " ")
        else:
            command = "{0} pandoc --from=markdown --to=rst --output=README.rst README.md".format(PIPENV).strip().split(
                " ")
        execute(*(command))


@task()
@skip_if_no_change("mypy")
@timed()
def mypy():
    """
    Are types ok?
    """
    if sys.version_info < (3, 4):
        print("Mypy doesn't work on python < 3.4")
        return
    if IS_TRAVIS:
        command = "{0} -m mypy {1} --ignore-missing-imports --strict".format(PYTHON, PROJECT_NAME).strip()
    else:
        command = "{0} mypy {1} --ignore-missing-imports --strict".format(PIPENV, PROJECT_NAME).strip()

    bash_process = subprocess.Popen(command.split(" "),
                                    # shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE
                                    )
    out, err = bash_process.communicate()  # wait
    mypy_file = "mypy_errors.txt"
    with open(mypy_file, "w+") as lint_file:
        lines = out.decode().split("\n")
        for line in lines:
            if "build_utils.py" in line:
                continue
            if "test.py" in line:
                continue
            if "tests.py" in line:
                continue
            if "/test_" in line:
                continue
            if "/tests_" in line:
                continue
            else:
                lint_file.writelines([line + "\n"])

    num_lines = sum(1 for line in open(mypy_file) if line and line.strip(" \n"))
    max_lines = 25
    if num_lines > max_lines:
        raise TypeError("Too many lines of mypy : {0}, max {1}".format(num_lines, max_lines))


@task()
@timed()
def pin_dependencies():
    """
    Create requirement*.txt
    """
    with safe_cd(SRC):
        execute(*("{0} pipenv_to_requirements".format(PIPENV).strip().split(" ")))


@task()
@timed()
def jiggle_version():
    with safe_cd(SRC):
        command = "{0} jiggle_version here --module={1}".format(PIPENV, PROJECT_NAME).strip()
        execute(*(command.split(" ")))


@task()
@timed()
def check_setup_py():
    # deprecated in favor of twine check.
    return
    # if
    # ValueError: ZIP does not support timestamps before 1980
    # then run this to ID
    #   find . -mtime +13700 -ls
    with safe_cd(SRC):
        if IS_TRAVIS:
            execute(PYTHON, *("setup.py check -r -s".split(" ")))
        else:
            execute(*("{0} {1} setup.py check -r -s".format(PIPENV, PYTHON).strip().split(" ")))


@task()
@skip_if_no_change("vulture", expect_files="dead_code.txt")
@timed()
def dead_code():
    """
    This also finds code you are working on today!
    """
    with safe_cd(SRC):
        if IS_TRAVIS:
            command = "{0} vulture {1}".format(PYTHON, PROJECT_NAME).strip().split()
        else:
            command = "{0} vulture {1}".format(PIPENV, PROJECT_NAME).strip().split()

        output_file_name = "dead_code.txt"
        with open(output_file_name, "w") as outfile:
            env = config_pythonpath()
            subprocess.call(command, stdout=outfile, env=env)

        cutoff = 1000
        print("High cutt off for dead code because not even out of beta")
        num_lines = sum(1 for line in open(output_file_name) if line)
        if num_lines > cutoff:
            print("Too many lines of dead code : {0}, max {1}".format(num_lines, cutoff))
            exit(-1)


@task(compile_mark_down, formatting, mypy, detect_secrets, git_secrets, dead_code, nose_tests, coverage, compile_py,
      lint,
      check_setup_py, pin_dependencies, jiggle_version)  # docs ... later
@skip_if_no_change("package")
@timed()
def package():
    """
    package, but don't upload
    """
    with safe_cd(SRC):
        for folder in ["build", "dist", PROJECT_NAME + ".egg-info"]:
            execute("rm", "-rf", folder)

    with safe_cd(SRC):
        execute(PYTHON, "setup.py", "sdist", "--formats=gztar,zip")

    with safe_cd(SRC):
        execute("twine", "check", "dist/*.gz")


@task(package)
@timed()
def gemfury():
    """
    Push to gem fury, a repo with private options
    """
    # fury login
    # fury push dist/*.gz --as=YOUR_ACCT
    # fury push dist/*.whl --as=YOUR_ACCT

    cp = subprocess.run(("fury login --as={0}".format(GEM_FURY).split(" ")),
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        shell=False, check=True)
    print(cp.stdout)

    about = {}
    with open(os.path.join(SRC, PROJECT_NAME, "__version__.py")) as f:
        exec(f.read(), about)
    version = Version(about["__version__"])
    print("Have version : " + str(version))
    print("Preparing to upload")

    if version not in get_versions():
        for kind in ["gz", "whl"]:
            try:
                files = glob.glob("{0}dist/*.{1}".format(SRC.replace(".", ""), kind))
                for file_name in files:
                    cp = subprocess.run(("fury push {0} --as={1}".format(file_name, GEM_FURY).split(" ")),
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        shell=False, check=True)
                    print("result of fury push")
                    for stream in [cp.stdout, cp.stderr]:
                        if stream:
                            for line in stream.decode().split("\n"):
                                print(line)

            except subprocess.CalledProcessError as cpe:
                print("result of fury push- got error")
                for stream in [cp.stdout, cp.stderr]:
                    if stream:
                        for line in stream.decode().split("\n"):
                            print(line)
                print(cpe)
                raise


# FAST. FATAL ERRORS. DON'T CHANGE THINGS THAT CHECK IN
@task(mypy, detect_secrets, git_secrets, check_setup_py, compile_py, dead_code)
@skip_if_no_change("pre_commit_hook")
@timed()
def pre_commit_hook():
    # Don't format or update version
    # Don't do slow stuff- discourages frequent check in
    # Run checks that are likely to have FATAL errors, not just sloppy coding.
    pass


# Don't break the build, but don't change source tree either.
@task(mypy, detect_secrets, git_secrets, nose_tests, coverage, check_setup_py, compile_py, dead_code)
@skip_if_no_change("pre_push_hook")
@timed()
def pre_push_hook():
    # Don't format or update version
    # Don't do slow stuff- discourages frequent check in
    # Run checks that are likely to have FATAL errors, not just sloppy coding.
    pass


def do_check_manifest(output_file_name, env):
    if IS_TRAVIS:
        command = "check-manifest".format(PYTHON).strip().split()
    else:
        command = "{0} check-manifest".format(PIPENV).strip().split()

    with open(output_file_name, "w") as outfile:

        subprocess.call(command, stdout=outfile, env=env)


@task()
@skip_if_no_change("check_manifest", "manifest_errors.txt")
@timed()
def check_manifest():
    env = config_pythonpath()
    output_file_name = "manifest_errors.txt"
    do_check_manifest(output_file_name, env)

    with open(output_file_name) as outfile_reader:
        text = outfile_reader.read()

        print(text)
        if not os.path.isfile("MANIFEST.in") and "no MANIFEST.in found" in text:
            command = "{0} check-manifest -c".format(PIPENV).strip().split()
            subprocess.call(command, env=env)
            # print("Had to create MANIFEST.in, please review and redo")
            do_check_manifest(output_file_name, env)
        else:
            pass
            # print("found it")
    cutoff = 20
    num_lines = sum(1 for line in open(output_file_name) if line)
    if num_lines > cutoff:
        print("Too many lines of manifest problems : {0}, max {1}".format(num_lines, cutoff))
        exit(-1)


@task()
@timed()
def echo(*args, **kwargs):
    """
    Pure diagnostics
    """
    print(args)
    print(kwargs)


# Default task (if specified) is run when no task is specified in the command line
# make sure you define the variable __DEFAULT__ after the task is defined
# A good convention is to define it at the end of the module
# __DEFAULT__ is an optional member

__DEFAULT__ = echo

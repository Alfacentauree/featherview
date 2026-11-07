#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <libgen.h>
#include <limits.h>

int main(int argc, char *argv[]) {
    char exe_path[PATH_MAX];
    ssize_t len = readlink("/proc/self/exe", exe_path, sizeof(exe_path) - 1);
    if (len != -1) {
        exe_path[len] = '\0';
    } else {
        strncpy(exe_path, argv[0], sizeof(exe_path) - 1);
        exe_path[sizeof(exe_path) - 1] = '\0';
    }

    char *dir = dirname(strdup(exe_path));
    char py_path[PATH_MAX];

    // Check sibling featherview app directory or parent directory
    snprintf(py_path, sizeof(py_path), "%s/..", dir);

    // Update PYTHONPATH
    const char *old_pypath = getenv("PYTHONPATH");
    char new_pypath[PATH_MAX * 2];
    if (old_pypath && strlen(old_pypath) > 0) {
        snprintf(new_pypath, sizeof(new_pypath), "%s:%s", py_path, old_pypath);
    } else {
        snprintf(new_pypath, sizeof(new_pypath), "%s", py_path);
    }
    setenv("PYTHONPATH", new_pypath, 1);

    // Prepare arguments for execvp
    char **new_argv = malloc((argc + 3) * sizeof(char *));
    new_argv[0] = "python3";
    new_argv[1] = "-m";
    new_argv[2] = "featherview.app";

    for (int i = 1; i < argc; i++) {
        new_argv[i + 2] = argv[i];
    }
    new_argv[argc + 2] = NULL;

    execvp("python3", new_argv);

    perror("Failed to execute featherview");
    return 1;
}

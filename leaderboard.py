import os
from sys import argv, exit, stderr, stdout
from datetime import datetime as dt
import subprocess
import pickle
import re
import math
import sys


def find_executable():
    """
    Find the path to the DARTS executable.
    Try build/$<config> directory first, then build directory.
    """

    root = os.getcwd()
    darts = ""
    extension = ".exe" if os.name == "nt" else ""

    if os.path.exists(os.path.join(root, "build", "Release", f"darts{extension}")):
        darts = os.path.join(root, "build", "Release", f"darts{extension}")
    elif os.path.exists(os.path.join(root, "build", f"darts{extension}")):
        darts = os.path.join(root, "build", f"darts{extension}")
    else:
        print("Missing build dir\n")
        return None, None

    return darts, root


def render_image(exe_path, root_path):
    """
    Render the image and retrieve the intersection metrics
    """

    scene_dir = os.path.join(root_path, "scenes", "assignment2")
    scene_name = "leaderboard"
    scene_file = os.path.join(scene_dir, scene_name + ".json")

    start_time = dt.now()

    print("Starting render.... this may take a bit... ")
    proc = subprocess.Popen(
        [exe_path, scene_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stdout_lines = []
    stderr_lines = []

    # Read stdout and stderr in real-time
    for stdout_line in iter(proc.stdout.readline, ""):
        print(stdout_line, end="")
        stdout_lines.append(stdout_line)
    for stderr_line in iter(proc.stderr.readline, ""):
        print(stderr_line, end="")
        stderr_lines.append(stderr_line)

    proc.stdout.close()
    proc.stderr.close()
    proc.wait()

    print("Finished rendering image")

    out = "".join(stdout_lines)
    err = "".join(stderr_lines)

    stats_loc = out.find("Statistics:")
    intersections = out.find("Total intersection tests per ray")
    nodes = out.find("Nodes visited per ray")

    tri_str = out[intersections:]
    tri_str_nodes = out[nodes:]

    intersection_pattern = re.compile(r".*\s+\b(\d+)\b.*\s+\b(\d+)\b")

    match = intersection_pattern.match(tri_str.strip())
    match_nodes = intersection_pattern.match(tri_str_nodes.strip())

    files = [
        os.path.join(scene_dir, fname)
        for fname in os.listdir(scene_dir)
        if fname.startswith(scene_name) and fname.endswith(".png")
    ]

    files.sort(key=lambda x: os.path.getmtime(x))

    most_recent_img = files[-1]
    end_time = dt.now()

    intersections = float(match.group(1)) / float(match.group(2))
    nodes = float(match_nodes.group(1)) / float(match_nodes.group(2))

    return most_recent_img, intersections, nodes, start_time, end_time


def create_hash(
    img_path, intersections, nodes, publicize_results, time_start, time_end
):
    outfile = open("leaderboard.dat", "wb")
    img = open(img_path, "rb")

    pickle.dump(
        [intersections, nodes, publicize_results, time_start, time_end, img.read()],
        outfile,
        pickle.HIGHEST_PROTOCOL,
    )
    outfile.close()


def main():
    exe_path, scene_path = find_executable()
    if not exe_path:
        print(
            "Error: cannot find DARTS executable path, please ensure that you are running the leaderboard script from the darts directory, and that the darts executable has been built.",
            file=stderr,
        )
        exit(1)

    print("Executable located at:", exe_path)
    print("Scenes located at:", scene_path)
    print()

    # Note: make this True is if you want your results to be displayed on the class website leaderboard
    publicize_results = False
    if len(sys.argv) > 1:
        publicize_cmd = sys.argv[1]
        if publicize_cmd.strip() == "public":
            publicize_results = True

    img_path, intersections, nodes, time_start, time_end = render_image(
        exe_path, scene_path
    )

    print("Image path:", img_path)
    print()
    print(
        "Total intersection tests per ray:", math.floor(intersections * 100.0) / 100.0
    )
    print("Nodes visited per ray:", math.floor(nodes * 100.0) / 100.0)
    print("Figure of merit:", math.floor(nodes * intersections * 100.0) / 100.0)
    print()

    create_hash(img_path, intersections, nodes, publicize_results, time_start, time_end)


if __name__ == "__main__":
    main()

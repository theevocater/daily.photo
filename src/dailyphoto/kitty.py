import subprocess


def set_layout(layout: str) -> int:
    """
    Opens a new split window in kitten to show images in while editing metadata
    """
    return subprocess.call(
        [
            "kitten",
            "@",
            "goto-layout",
            layout,
        ],
    )


def new_window() -> str:
    """
    Opens a new split window in kitten to show images in while editing metadata
    """
    return subprocess.run(
        [
            "kitten",
            "@",
            "new-window",
            "--dont-take-focus",
            "--cwd",
            "current",
        ],
        capture_output=True,
    ).stdout.decode("utf-8")


def close_window(id: str) -> int:
    """
    Closes the  split window indicated by id
    """
    return subprocess.call(["kitten", "@", "close-window", f"--match=id:{id}"])


def open_image(image_name: str, window_id: str) -> int:
    """
    Show the image in the kitty window_id using icat
    """
    return subprocess.call(
        [
            "kitten",
            "@",
            "send-text",
            "--match",
            f"id:{window_id}",
            f"kitten icat {image_name}\n",
        ],
    )

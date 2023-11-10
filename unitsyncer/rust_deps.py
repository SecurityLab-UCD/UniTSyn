import re
import subprocess


def process(raw_stat: str) -> list[str]:
    """process the raw `rust-analyzer analysis-stats` to a list of function dependencies

    Args:
        raw_stat (str): stdout of `rust-analyzer analysis-stats`

    Returns:
        list[str]: list of function dependencies
    """
    # The regex pattern to match "{number}/{number} {number}% processing: "
    pattern = r"\d+/\d+ \d+% processing: "

    output_string = re.sub(pattern, "\n", raw_stat)
    return [l.strip() for l in output_string.split("\n")]


def get_analysis_stats(workdir: str) -> list[str]:
    """get workdir's function dependencies analysis

    Args:
        workdir (str): path to workspace folder

    Returns:
        list[str]: list of function dependencies
    """
    p = subprocess.run(
        ["rust-analyzer", "analysis-stats", workdir],
        capture_output=True,
        text=True,
    )
    raw_data = p.stdout.replace("\x08", "")
    return process(raw_data)


def main():
    # with open("stat") as f:
    #     raw_stat = f.read().replace("\x08", "")
    # # stat = stat.split("processing: ")
    # deps = process(raw_stat)
    # print(len(deps))
    # print(deps)
    workdir = "data/repos/marshallpierce-rust-base64/marshallpierce-rust-base64-4ef33cc"
    stats = get_analysis_stats(workdir)
    print(len(stats))
    print(stats)


if __name__ == "__main__":
    main()

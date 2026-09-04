#!/usr/bin/env python3
"""Download the free Whisper model once so the first edit does not pause."""

import argparse

from faster_whisper import WhisperModel


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="small")
    args = parser.parse_args()
    print(f"Downloading free Whisper model: {args.model}")
    WhisperModel(args.model, device="cpu", compute_type="int8")
    print(f"Whisper model ready: {args.model}")


if __name__ == "__main__":
    main()

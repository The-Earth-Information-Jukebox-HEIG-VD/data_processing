import argparse
import os
import cv2
import numpy as np
from tqdm import tqdm


def main():
    parser = argparse.ArgumentParser(
        description="Extract and resample annual NASA nightlights video into .npy arrays."
    )
    parser.add_argument(
        "video", type=str, help="Path or URL to the input nightlights MP4 video file."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="./nightlights_frames",
        help="Directory to save individual .npy files.",
    )
    parser.add_argument(
        "--target_width",
        type=int,
        default=1440,
        help="Target grid width (must be >= 1440).",
    )
    parser.add_argument(
        "--target_height",
        type=int,
        default=720,
        help="Target grid height (must be >= 720).",
    )
    parser.add_argument(
        "--start_year",
        type=int,
        default=2012,
        help="Start year of the nightlights sequence.",
    )

    args = parser.parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    # Open the video file
    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {args.video}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"-> Total Video Frames Found: {total_frames}")

    frame_count = 0
    saved_count = 0

    with tqdm(
        total=total_frames, desc="Extracting Annual Nightlights", unit="frame"
    ) as pbar:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # 1. Calculate the exact year for this frame
            year = args.start_year + frame_count
            if year > 2023:
                break  # Stop if it goes past 2023

            # 2. Resample/Resize frame to target resolution (e.g., 1440x720)
            resized_frame = cv2.resize(
                frame,
                (args.target_width, args.target_height),
                interpolation=cv2.INTER_AREA,
            )

            # 3. Convert to grayscale and normalize intensity to [0.0, 1.0] float32
            gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
            normalized_frame = gray_frame.astype(np.float32) / 255.0

            # 4. Save immediately to disk as .npy
            filename = f"nightlights_{year}.npy"
            output_path = os.path.join(args.output_dir, filename)
            np.save(output_path, normalized_frame)

            pbar.set_postfix(
                year=year, resolution=f"{args.target_width}x{args.target_height}"
            )
            pbar.update(1)

            frame_count += 1
            saved_count += 1

    cap.release()
    print(
        f"\nDone! Successfully processed and saved {saved_count} annual frames (2012–2023) into '{args.output_dir}'."
    )


if __name__ == "__main__":
    main()

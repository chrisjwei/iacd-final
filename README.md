# IACD Final Project - Movies in Iambic Pentameter

### Summary
For my IACD final project I have written some code that uses subtitles to extract dialogue from movies and strings clips of dialogue together by finding rhyming phrases with the same number of syllables.
##### Getting Started
This Repo contains a single python file `main.py` which contains a couple variables you should tweak before running
 - `MOVIE_PATH_BASE_DIR` should be set to the directory where all your videos reside
 - `SUB_PATH_BASE_DIR` should be set to the directory where all your subtitles reside
 - `OUTPUT_FINAL` should be set to the base filename (no extension) for your output video(s)
 - `NUM_SEGMENTS_MAX` should be reduced if it is taking too long to process or you are getting a out of memory exception
 - `SELECTED_NUM_SYLLABLES` declares which number of syllables you care about in the output video

Your video files should be in mp4 format and your subtitles should be in SRT format and the filename bases should be the same: ex. `movies/Star_Wars_A_New_Hope.mp4`, `subs/Star_Wars_A_New_Hope.srt`.

##### Dependencies
`main.py` depends on multiple python libraries that can be easily installed using `pip install <dependency>`
 - `moviepy` for concatenating clips together
 - `numpy`
 - `pysrt` for reading srt files
 - `nltk` as well as the `cmudict` corpus

##### Features
 - Rhyming and syllable detection using pronuciation rules from `cmudict` shout outs to CMU
 - Standardizes movie height
 - Standardizes loudness of sound clips

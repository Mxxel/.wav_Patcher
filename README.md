# .wav_Patcher

Small Python 3 script that rewrites two bytes in a WAV header.
I wrote it because friends and me often had issues loading wave audio tracks we got from bandcamp.com. 
The issue occured when we were loading those tracks from USB sticks, after burning them as audio CD they played without issues.
I can say for 100% that the Pioneer CDJ-350 are affected of this bug, but i think this issue occured on other pioneer players also.
To solve the issue without the time that would be needed for converting each track, i researched the issue and this is the result:

## How to run it

No extra packages. From this directory:

```bash
python3 test.py -f /path/to/track.wav
python3 test.py -p /path/to/folder
```

`-f` and `-p` cannot be combined. One of them is required.

What those flags actually do is narrower than the help text:

- `-f` checks that the path you gave exists. If it does not, the script raises `File not found`. If it does, the script does **not** open that path. It always opens `/home/user/PycharmProjects/WaveModder/exopatch.wav`, the file the author used while testing. On any other machine that path is missing, so the run fails inside `patch_single_audio` unless that exact file is present.
- `-p` is accepted and then ignored. `main` never reads it. `scan_for_audiofiles_in_path` can list `.wav` files under a folder, and `patch_mutiple_files` is an empty function. Neither is called.

The patch itself lives in `patch_single_audio(file_path)`. That function does use the path it is given. The command-line menu does not pass your path through.

There is no backup. When the two-byte test matches, the same path is overwritten. The upstream `todo` file is the note `add overwrite and clone inkl. warnung` (add an overwrite and a copy, including a warning). That was not built.

## How the patch works

`patch_single_audio` does the following.

1. Prints `New file to get checked and maybe patched: ` plus the path.
2. Reads the whole file into a `bytearray`.
3. Looks only at indexes 20 and 21.
4. If they are `FE` then `FF`, it sets them to `01` then `00`, writes the whole buffer back over the same path, prints `Patching done... so maybe just give it a try ;D`, and returns `True`.
5. Otherwise it prints the path immediately followed by `must not be patched` (there is no space before "must"), changes nothing, and still returns `True`.
6. Any exception (file missing, file shorter than 22 bytes, disk error) is printed as `An error occurred during modification:` and the function returns `None`.

No other byte is read or written. The audio samples are copied through only because the whole file is written back.

### Why offsets 20 and 21 are the format code

The script does not search for chunk names. It assumes the usual WAV layout, where the format record starts at a fixed place:

| Offset | Size | What sits there in a normal WAV | Does this script touch it? |
| --- | --- | --- | --- |
| 0 | 4 | `RIFF` | no |
| 4 | 4 | RIFF size (file length minus 8) | no |
| 8 | 4 | `WAVE` | no |
| 12 | 4 | `fmt ` (the format chunk) | no, and not checked |
| 16 | 4 | size of the format chunk | no |
| 20 | 2 | format code, `wFormatTag`, little-endian | **yes, the only test and the only edit** |
| 22 | 2 | channel count | no |
| 24 | 4 | sample rate | no |
| 28 | 4 | bytes per second | no |
| 32 | 2 | block align | no |
| 34 | 2 | bits per sample | no |
| 36 onward | varies | present when the format chunk is longer than 16 bytes: extra-byte count, valid bits, channel mask, subtype GUID | no |

Those field names are the Microsoft `WAVEFORMATEX` / `WAVEFORMATEXTENSIBLE` layout ([WAVEFORMATEX](https://learn.microsoft.com/en-us/windows/win32/api/mmreg/ns-mmreg-waveformatex)). The script never checks that offset 12 really is `fmt `. The indexes are meaningful for a file that uses this layout, which is the layout the author patched.

WAV stores the 16-bit format code least-significant byte first:

- `FE FF` is the integer `0xFFFE` (65534). Microsoft's name for that tag is `WAVE_FORMAT_EXTENSIBLE`: the format chunk continues with the extra fields above, and the real subtype is a GUID later in the chunk.
- `01 00` is the integer `0x0001` (1). That tag is `WAVE_FORMAT_PCM`: integer PCM, which is what the script writes.

So the broken-versus-fine test in this program is exactly one comparison. A file whose bytes 20 and 21 are `FE FF` is rewritten. A file with any other pair, including a Bandcamp WAV that is already `01 00`, is left byte-for-byte alone.

## The issue it is aimed at

Some WAVs downloaded from bandcamp.com will not load or play on some CD players. A reported case is the Pioneer CDJ-350: the player shows E-8305 (unsupported file format) for those downloads, while other WAV files, including other Bandcamp downloads, play. The same two-byte pattern is what this script selects.

This script does not mention Bandcamp or the CDJ-350 by name. It says Pioneer CD players will not read the files over USB. Two public notes describe the same edit and the same symptom:

- Pioneer DJ staff ("Pulse"), on a CDJ-350 thread where 16-bit WAVs played and the Bandcamp WAVs did not, called it a Bandcamp "PCM stream type flag" problem. The staff fix is the same change this script makes: set bytes 20–21 (`wFormatTag`) to `01 00`, meaning PCM. rekordbox ignores the flag; the CDJ does not. Thread: [E 8305 error CDJ 350 but file types are correct](https://forums.pioneerdj.com/hc/en-us/community/posts/360061678611-E-8305-error-CDJ-350-but-file-types-are-correct) (26 Apr 2020).
- The same staff wording, "enhanced multichannel audio," is how they described the flag. The audio bytes are not what the player is refusing. It refuses the format code before it treats the file as playable PCM.

The author's own check matches that outcome: after this rewrite, their Pioneer CDJ played the file from USB (upstream commit message, 2 Aug 2023).

### What is wrong with the affected files

On a normal WAV, `FE FF` marks the file as `WAVE_FORMAT_EXTENSIBLE` instead of plain PCM. Microsoft defines that tag for a format the basic PCM structure was not meant to describe by itself: more than two channels, or a sample whose valid bit count does not fill its container. The same docs say the plain PCM tag is for 8- or 16-bit samples, and that sample sizes above 16 bits can be described with the extensible structure ([WAVEFORMATEX on mmeapi.h](https://learn.microsoft.com/en-us/windows/win32/api/mmeapi/ns-mmeapi-waveformatex)).

Encoders still write `FE FF` on ordinary stereo files, especially 24-bit ones, even when the samples are plain stereo PCM. On the CDJ-350 reports above, that tag is what the player rejects (E-8305). Pioneer staff said rekordbox ignores the same flag. The file can look fine in rekordbox and still fail on the player.

This script's answer is to relabel those two bytes as PCM (`01 00`) and leave the samples alone. It does not remove the extra extensible fields that may still follow. Pioneer staff described that two-byte edit as sufficient, and it is the only edit this script performs. The author's CDJ played the result.

### Why other Bandcamp WAVs do not have the problem

Bandcamp is not doing one thing to every download. This program's split, and the split in the CDJ-350 report, is the format code at offsets 20 and 21:

- Affected file: those bytes are `FE FF`. The player treats the file as extensible rather than PCM and will not load it. This script rewrites that pair.
- Fine file: those bytes are already something else, in the working case `01 00` (plain PCM). This script prints that the file must not be patched and does not modify it. A player that accepts PCM has nothing in that field to reject.

The script does not measure bit depth, so it is not evidence that every 24-bit Bandcamp WAV fails or that every 16-bit one works. A 24-bit file that is already tagged `01 00` is skipped. A 16-bit file tagged `FE FF` would be patched. Public writeups connect `FE FF` with 24-bit exports because that is when encoders commonly choose the extensible tag (the Pioneer forum note cites ffmpeg doing this for anything above 16-bit: [Changing the WAV-Header to meet CDJs standard](https://forums.pioneerdj.com/hc/en-us/community/posts/4410137950233-Changing-the-WAV-Header-to-meet-CDJs-standard)). Which Bandcamp release was encoded which way is not recorded in this program. The only difference it uses is that byte pair.

## Todo, feel free to contribute:

- It does not patch the path you pass with `-f`, and `-p` does nothing. See above.
- It does not copy the file or warn before overwriting.
- It does not walk chunks. If `fmt ` is not the first chunk (a `JUNK` or `bext` chunk first, or an ID3 tag in front of `RIFF`), offsets 20 and 21 are not the format code. The script can then skip a file that needed the edit, or overwrite two unrelated bytes. It never looks at ID3, RIFF size, alignment, or chunk type.
- It does not check the subtype GUID. An extensible file that is actually float, or actually more than two channels, is relabeled PCM with its samples unchanged. The author reported one Pioneer CDJ playback after the edit, not a general test of those files.
- It does not change bit depth, sample rate, or channel count. A file the player rejects for a rate or depth it cannot play stays rejected. The CDJ-350 reports that prompted the two-byte fix were files the player was specified to accept apart from this flag; this script does not check that.
- It does not turn a non-`FE FF` tag into PCM. IEEE float (`03 00` at those offsets) is skipped. So is any other code.
- It does not shrink the format chunk. After a successful run the file can still carry the extensible tail under a PCM tag. That is the edit the author and the Pioneer staff note both used.
- A return value of `True` means the function finished. It also returns `True` when it decided not to patch.

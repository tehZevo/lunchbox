# Lunchbox
*Novation Launchpad X API / controller*

## Installing
`pip install git+https://github.com/tehzevo/lunchbox.git`

## Controller
To run the controller script, run `$ lunchbox`.

### Features
* Configurable isomorphic layout - see `controller-config.yml` for an example
* Launchpad X autodetection with each Launchpad getting its own (configurable) octave offset
* Transposing: up/down arrows transpose octaves, left/right arrows transpose semitones, and *Session* resets transpose to 0
* 8-midi channel selection - right-side buttons function as midi channel selection

## Visualizer
For visualizer functionality, make sure to install with the visualizer extra:
`pip install "lunchbox[visualizer] @ git+https://github.com/tehzevo/lunchbox.git"` or
`pip install "git+https://github.com/tehzevo/lunchbox.git#egg=lunchbox[visualizer]"`.
Then, when creating your `Lunchbox` instance, set `Lunchbox(visualizer=True, ...)`.

## API
*See `example.py`*

## Authors
* [tehZevo](https://github.com/tehZevo)
* [Kaydax](https://github.com/Kaydax)

## Ideas
- "contact point"-based notes: portamento/"throwing" notes

## TODO
- stop swallowing exceptions (mido issue?)
- unplug/replug detection
- visualizer for controller
- pitch bend via polytouch

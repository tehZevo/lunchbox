# Lunchbox
*Novation Launchpad X API / controller*

## Installing
`pip install git+https://github.com/tehzevo/lunchbox.git`

## Controller
The included controller script is a configurable isomorphic layout controller. To run the script, run `$ lunchbox`.
In this mode, the up/down arrows transpose up/down an octave, and the left/right transpose up/down by one semitone.
Press the *Session* button to reset transpose to default.
The controller should autodetect all connected Launchpad X and give them a (configurable) octave offset.
Create a `controller-config.yml` to configure and take a look at this repo's `controller-config.yml` for more configuration options.

## API
*See `example.py`*

## Authors
* [tehZevo](https://github.com/tehZevo)
* [Kaydax](https://github.com/Kaydax)

## TODO
- stop swallowing exceptions (mido issue?)
- unplug/replug detection
- visualizer for controller
- pitch bend via polytouch
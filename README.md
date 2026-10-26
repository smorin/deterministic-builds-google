# One Environment, N Machines: Deterministic Builds for Humans and Agents

Demo repository and slide deck for a 25 minute talk at Google (October 26, 2026).

**Speaker:** Steve Morin ([@smorin](https://github.com/smorin)), Flox

## What is in here

```
.flox/env/manifest.toml   one file: runtime, database, agent harness, services, hermetic build
.flox/env/manifest.lock   the receipt: exact versions and store paths for 3 systems
app.py                    tiny HTTP service that reports exactly what it was built from
scripts/sbom.py           SPDX 2.3 SBOM derived from manifest.lock (not a scan)
slides/index.html         the deck, self contained, no network needed on stage
slides/script.md          the spoken script, one section per slide, with cue marks for each command
.github/workflows/ci.yml  "machine 2 of 3": an x86_64-linux runner activating the same lock
```

## Run the demo

Install Flox from [flox.dev/download](https://flox.dev/download) (or `brew install flox`), then:

```sh
git clone https://github.com/smorin/deterministic-builds-google && cd deterministic-builds-google

flox activate -s                       # enter the env and start redis + app
python3 --version                      # Python 3.14.7, on every machine
flox services status
curl -s localhost:8080                 # {"python": "3.14.7", "redis": "PONG", ...}

flox build                             # hermetic (sandbox = "pure") build
./result-app/bin/app --version

flox containerize --runtime docker     # OCI image, no Dockerfile
docker run --rm -v "$PWD:/w" -w /w deterministic-builds-google:latest python3 app.py --report
python3 scripts/sbom.py | jq '.packages[] | {name, versionInfo, licenseConcluded}'
```

Under the hood (plain Nix, no Flox involved; needs `nix-command` and `flakes`
in `experimental-features`):

```sh
flox activate -- sh -c 'realpath "$(which python3)"'       # /nix/store/0kcws5…-python3-3.14.7/bin/python3.14
nix-store -q --references /nix/store/0kcws5blwbdyxqxjd1w8hjipz61xny3k-python3-3.14.7 | head -6
nix-store -q --requisites /nix/store/0kcws5blwbdyxqxjd1w8hjipz61xny3k-python3-3.14.7 | wc -l   # 51: the closure
nix derivation show "$(nix-store -q --deriver /nix/store/0kcws5blwbdyxqxjd1w8hjipz61xny3k-python3-3.14.7)" \
  | jq '.[] | {system, builder, inputDrvs: (.inputDrvs|length), inputSrcs: (.inputSrcs|length), out: .outputs.out.path}'

# The lock is a pointer into nixpkgs. Plain nix reproduces the exact same store path:
jq -r '.packages[] | select(.install_id=="python3" and .system=="aarch64-darwin") | .locked_url, .attr_path, .outputs.out' .flox/env/manifest.lock
nix build 'github:NixOS/nixpkgs/7fd4004d0511991fff3a0524856a9be09e28c5f0#python3' --no-link --print-out-paths
```

Same lock, three systems:

```sh
shasum -a 256 .flox/env/manifest.lock  # 6d746f718ac79d288b3327150d43df25d71c6f254d73f0ed0eedceedcbca6bd9
                                       # identical on darwin and linux
jq -r '[.packages[].locked_url] | unique[]' .flox/env/manifest.lock
```

## The deck

Open `slides/index.html` in a browser (or the
[GitHub Pages copy](https://smorin.github.io/deterministic-builds-google/slides/)).
Terminal slides type each command when you press `→`, then reveal the output.

| Key | Action |
|-----|--------|
| `→` `space` | run next command, or go to next slide |
| `←` | previous slide (terminals shown completed) |
| `n` | speaker notes with per slide time targets |
| `t` | start or reset the talk clock (turns red when a slide runs a minute late) |
| `f` | fullscreen |
| `?` | help |

Every terminal output in the deck was captured from a real run of this
repository on 2026-10-16 with flox 1.18.0; the plain `nix` commands in the
"Under the hood" section were captured on 2026-10-17 with nix 2.31.5 against
the same `manifest.lock`. For this Google version, names in that output were
changed after capture (`deterministic-builds-ATO` to `deterministic-builds-google`,
`ato-demo` to `google-demo`, and the GitHub and FloxHub owner to `smorin`), and
the clone command on the three machine slide was corrected. Versions, hashes, and
store paths are as captured. Because `app.py` changed, a fresh `flox build` prints
a different `app-0.1.0` store path than the build slide shows. Three things are emulated and marked as such in the
speaker notes:

- The `ci-runner` and `agent-sandbox` panes on the three machine slide. Their
  versions and store paths are the real ones from `manifest.lock`; the machines
  were not on my desk.
- `flox activate -r smorin/deterministic-builds-google`. Run `flox push` from
  this repo before the talk and that step works live.
- The `claude -p ...` transcript. Every command in it is real and `nodejs@22.21.1`
  is what the catalog resolves today.

## Talk outline (25 min)

| Time | Section |
|------|---------|
| 0:00 | Title |
| 1:00 | The problem: where is your software being built? |
| 3:00 | What setup looks like today: four machines, four install stories |
| 4:30 | Two problems: same build everywhere, same run wherever it lands next |
| 6:00 | The fix: declare it, don't script it (manifest, lock, closure) |
| 7:30 | Under the hood: how Nix works (store paths, references, closures, derivations) |
| 9:45 | What Nix gives you and what it asks of you; the alternatives |
| 10:30 | Flox on top of Nix: what it adds, what it leaves alone |
| 11:30 | Same lock, plain `nix build`, same store path |
| 12:00 | What is open source (Nix, nixpkgs, flox, flox-skills) and what is hosted |
| 12:30 | Demo 1: one file |
| 16:30 | Demo 2: three machines, one hash |
| 19:30 | Demo 3: the artifact and the receipt (build, containerize, SBOM) |
| 22:30 | Humans and agents share one definition |
| 24:00 | Takeaway and links |

# One Environment, N Machines — talk script (25 min)

Spoken script for `slides/index.html`, one section per slide. Times are the
clock targets shown in the deck (press `t` to start the clock). **[→]** marks
the moment to press the right arrow so a terminal command types out; the words
right after it are what you say while it types and the output lands.

Pace: about 140 words a minute. Each section lists its word budget so you can
trim on the day. Total is about 3,300 spoken words, which is 24 minutes of
talking plus the typing pauses and the show of hands.

---

## 1 · Title — 0:00 (≈140 words)

Hi, I'm Steve. I'm VP of Engineering at Flox, and I want to say up front
what that means for the next 25 minutes: I'm going to show you two layers of
open source software, Nix and Flox, and I'm going to tell you exactly which
parts are open source and which parts are hosted services, because you should
know that before you decide to use any of it.

Quick show of hands. Think about the last environment your code ran in. Not
your laptop, the last one. A CI runner, a container, a sandbox an agent spun
up. Raise your hand if a human set that machine up.

[pause]

Yeah. Most of the room keeps their hands down. That's the talk. Software gets
built everywhere now, and almost none of those "everywheres" were set up by a
person. So what sets them up, and can we make them agree with each other?

## 2 · Where is your software being built? — 1:00 (≈210 words)

Let's count the machines. Left to right.

Your laptop. Set up by you, slowly, once, probably two jobs ago. It has drifted
ever since. There's a Python in there you don't remember installing.

CI. A fleet of runners set up by a YAML file and whatever the base image
happened to contain that morning. When the image updates, your build changes,
and nobody told you.

A local sandbox. A container, built by someone, somewhere, from a Dockerfile
that nobody has read end to end since it was written.

And the fourth one is new. A remote sandbox set up by the agent that is about
to run your tests in it. It reads your README, it guesses at a Python version,
it apt-gets something, and then it tells you the tests passed. In what,
exactly?

Four machines, four different setup stories, one codebase. And notice the
trend across the row: the setup is being done by less and less human
judgement each step. Human, script, image, model. That's not a complaint about
agents. It's just where the ground is now.

## 3 · Nobody sets these machines up by hand anymore — 2:30 (≈60 words)

Nobody sets these machines up by hand anymore. And on the rare occasion
somebody does, every one of them does it a little differently.

So let's be honest about what "setup" actually looks like today, for one
repository.

## 4 · Four machines, four install stories — 3:00 (≈210 words)

This is the real README for a small service. One Python app, Redis behind it,
jq for scripts, and Claude Code as the agent harness, because the agent's
tooling is part of the environment too.

On macOS, Homebrew. `brew install python@3.14`. Fine.

In CI, Ubuntu's apt. Look at the comment. That gives you Python 3.12 and
Redis 7. Nobody chose 3.12. It's what the distro ships.

The Dockerfile starts from `python:3.13-slim`. That's a third Python. Also not
chosen. It was the tag someone copied from a tutorial.

And then there's a `curl | sh`. We all do it. It fetches whatever is at that
URL today.

And the agent? The agent reads all of the above, picks one of them, and hopes.
And when the tests go red on CI and green on your laptop, you spend an
afternoon finding out that 3.12 and 3.14 disagree about something small.

Three Pythons, two Redises, one piped shell script. Same repo. None of it is
anyone's fault. It's just that each machine has its own package manager with
its own idea of "latest".

## 5 · Build it the same. Run it the same. — 4:30 (≈200 words)

Two problems fall out of that, and I want to separate them because they have
the same fix but different shapes.

Problem one: the same build, on every machine. Laptop, CI runner, local
sandbox, agent sandbox. One definition of the toolchain, reproduced exactly,
so that a green build means the same thing wherever it happened.

Problem two: the same run, wherever the thing lands next. Another runner, a
container, production, or the same box six months from now when somebody
needs to rebuild an old release. The artifact should carry everything it
depends on, so it doesn't matter what the host happened to have.

And the line at the bottom is the one I'd like you to take home even if you
forget the rest. When you put a model in the loop, the model's reasoning is
the one part of the system that is supposed to vary. Everything underneath it
should be boring and identical. If the environment is also varying, you can't
tell which one caused the difference.

## 6 · Declare it. Don't script it. — 6:00 (≈210 words)

Here's the shape of the fix. It's not new. It's the shape every lockfile-based
package manager has, applied to the whole machine instead of one language.

You write a manifest. It names what you want: Python 3.14, Redis, jq, the
agent's harness. It doesn't say how to install them.

A tool resolves that to a lock. The lock has exact versions and exact store
paths for every system you care about: Apple Silicon, x86 Linux, ARM Linux.
Same file, three columns.

The lock pins a closure, which is a word I'll define properly in a minute. For
now: a directory tree whose name is a hash of everything that went into it.

And then every verb reads from that same closure. Activate gives you a shell
with services. Build gives you a hermetic artifact. Containerize gives you an
image with no Dockerfile. Publish shares the package.

The engine doing all of this is Nix. Flox is a layer on top of it. And I don't
want to wave at Nix and move on, because the hashes you're about to see in the
demos only mean something if you know where they come from. So, five minutes
on the engine.

## 7 · Section: What Nix actually does — 7:30 (≈40 words)

If you already run Nix, the next three slides will be review, and the
interesting part for you is where Flox sits. If you've bounced off Nix before,
this is the version without the language.

## 8 · Every package lives at a path that is a hash of its inputs — 7:45 (≈110 words)

This is the real path of the Python in this repository.

Everything Nix builds lands in `/nix/store`, in a directory named with a hash
and then a human-readable name. The hash is computed from every input: the
source tarball, every dependency by their own hashes, the build script, the
configure flags, the target system. The name after the dash is for you. Nix
never looks anything up by name.

Three things follow from that. Nothing goes into `/usr/lib`; every build gets
its own directory, written once, never edited. Dependencies are absolute store
paths, fixed at build time, so there's no search path to get wrong. And if you
change any input you get a new hash, next to the old one. Two Pythons never
fight.

## 9 · Terminal: references, closure, derivation — 8:30 (≈180 words)

Let me show you that with plain `nix` commands. Nothing Flox-specific on this
slide.

**[→]** First, where does `python3` actually live? Resolve the symlinks.
There's the store path, and the hash matches the one on the last slide.

**[→]** What does it point at? These are its direct references. Six of
eighteen. Every one is an exact store path: this bzip2, this zlib, this
sqlite. Not "whichever libssl the linker finds".

**[→]** Now follow those references all the way down. That's the closure: the
package plus everything it transitively needs. Fifty-one paths. When I said
"the artifact carries everything it depends on" two slides ago, this is the
thing it carries.

**[→]** Where did the package come from? Every store path has a deriver, a
`.drv` file. That's the recipe.

**[→]** And here's the recipe, summarized. A target system. A builder, which
is just bash, itself from the store. Twenty-one input derivations, six source
files. And the output path, computed from all of that before anything is
built. Same recipe on any machine gives the same path. That's the whole trick,
and it's twenty years old.

## 10 · What Nix gives you. What it asks of you. — 9:45 (≈110 words)

I want to be fair about the trade, because this is the part people usually
skip.

Nix gives you that store. It gives you nixpkgs, which is over a hundred
thousand package recipes in one git repository, so one commit pins all of
them. It gives you binary caches, so a build done once can be fetched
everywhere as the same bytes. And it gives you sandboxed builds with no
network, no home directory, no `/usr`.

What it asks: learn the Nix language, which is lazy and functional and its own
thing. Pick a pinning story. Write a derivation for anything not already
packaged. And think per platform.

Flox is one answer to the right-hand column. devenv, devbox, and plain flakes
are others. Pick the one that fits your team.

## 11 · Flox on top of Nix — 10:30 (≈150 words)

So here's where Flox sits. Top to bottom.

You write TOML. Names, version constraints, environment variables, services, a
build recipe, and the list of systems you care about.

The Flox CLI, which is GPL-2 and on GitHub, resolves each name to a specific
nixpkgs commit, writes the lock with a store path per system, composes the
environment, and drives the sandboxed build and the container image. It does
that by calling Nix.

Nix does what Nix always does: evaluate derivations, fetch from a cache or
build, own the store.

nixpkgs is where the recipes live.

On the right is the division of labor. Flox adds TOML instead of the Nix
language, version constraints resolved against an index of every nixpkgs
revision, one lock for every system, services and builds in the same file,
and a way to push and pull whole environments. Flox does not change the store,
the hashes, or the packages. Which means you can check that claim.

## 12 · Terminal: same lock, plain nix build — 11:30 (≈80 words)

**[→]** Here's the lock entry for Python on this laptop. A nixpkgs commit, an
attribute name, and the store path that commit produces for this system.

**[→]** So ask Nix directly, with no Flox involved, to build that attribute at
that commit, from upstream nixpkgs.

Same path. Character for character. The lock is a pointer into public
nixpkgs. If Flox vanished tomorrow, every path in that lockfile is one
`nix build` away.

## 13 · All of it is open source — 12:00 (≈90 words)

The table. Nix, LGPL-2.1: the store, the builder, the sandbox, the language.
nixpkgs, MIT: the recipes, and the commit your lock points at. The Flox CLI,
GPL-2: manifest, lock, activate, build, containerize. And flox-skills,
Apache-2, which is what the agent uses in the last demo.

Now the footer, which I'm not going to skip. Two things are hosted by Flox:
the catalog that resolves a name like "python 3.14" to a commit, and FloxHub,
behind `flox push`. Your environment is two text files in your repo. Once it's
locked, activate and build need Nix and a binary cache, and you just watched
that work.

## 14 · Section: Demo 1 — 12:30 (≈30 words)

Okay. Demos. Everything you're about to see is captured output from a real run
of this repository. Three things are emulated and I'll say so when we get to
them.

## 15 · Terminal: init, install, list — 12:45 (≈170 words)

**[→]** `flox init` creates an environment in the current directory. That's a
`.flox` folder with a manifest in it. Nothing is installed yet, nothing
touches the rest of the machine.

**[→]** `flox install`, four packages. Python, Redis, jq, and Claude Code.
I want to point at that last one. The agent's harness is just another
package. It gets pinned the same way the runtime does, in the same file, with
the same hash. The warning is real: Claude Code has an unfree license, and
Flox tells you so, because the license is in the lock.

**[→]** `flox list`. Exact versions. Python 3.14.7, Redis 8.10.2, jq 1.8.2,
Claude Code 2.1.296. These came out of the catalog, which indexes every
nixpkgs revision, so what you get is a commit and a store path, not "latest".
That's the same commit and path you'd get from `nix build`, as we just saw.

## 16 · Terminal: the manifest — 14:00 (≈150 words)

**[→]** This is the whole thing. One file.

Top: the four packages, with a version constraint on Python. Then static
variables. Then two services: Redis, with its data directory inside the
environment's cache, and the app.

Then a build. The command is three lines of shell. `sandbox = "pure"` means
it runs in the Nix sandbox: no network, no home directory, only the tracked
sources and the manifest's packages. `runtime-packages` says the artifact
only needs Python and Redis in its closure, not jq, not the agent.

And at the bottom, systems. Apple Silicon, ARM Linux, x86 Linux. That one
line is what makes the next demo possible: the lock will carry a store path
for each of those.

You can write this file by hand. You can have the CLI write it. You can have
an agent write it. It's TOML, and it's in git.

## 17 · Terminal: activate with services — 15:00 (≈210 words)

**[→]** `flox activate -s`. You get a shell with everything on the path, and
the `-s` starts the services declared in the manifest. Redis and the app come
up.

**[→]** Ask the tools what they are. Python 3.14.7. Redis 8.10.2. Claude Code
2.1.296. The same numbers as the lock, because they are the lock.

**[→]** `flox services status`. Both running, with PIDs. These are real
processes managed by the environment, not containers.

**[→]** And curl the app. It reports what it was built from: the Python it's
running on, the system, the environment path, and that it can reach Redis.

What I'd like you to notice is what didn't happen. Nothing was installed into
`/usr/local`. Homebrew wasn't touched. There's no virtualenv. When I
`deactivate`, the machine is as it was. And if I'd done this on a Linux box
the commands would be identical, which is the next demo.

If you're a Nix person, you can get most of this slide from `nix shell` or a
flake dev shell. What the manifest adds here is the services block and the
version constraint. That's the honest size of the difference on a laptop.

## 18 · Section: Demo 2 — 16:30 (≈40 words)

Same git repo, three machines. An Apple Silicon laptop, an x86 CI runner, and
an ARM Linux sandbox for the agent. The laptop column is real. The two Linux
columns are emulated from the same lockfile; their store paths are the real
ones from the lock.

## 19 · Terminal: three machines — 16:45 (≈170 words)

**[→]** Clone the repo on all three.

**[→]** `flox activate -- python3 --version`. That form runs one command inside
the environment and exits. Three machines, three architectures. Python 3.14.7
on all of them. No Dockerfile, no setup script, no "install Python first".

**[→]** `flox list` on all three. Identical.

**[→]** And the hash of the lockfile. Identical, because it's the same file in
git. That's the point. The lockfile isn't generated per machine. It's resolved
once, for every system, and committed. Each machine just reads its own column.

So "works on my machine" stops being a sentence that means anything. The
machine isn't an input anymore. The only inputs are the manifest, the lock,
and your source.

For CI specifically: this repo has a GitHub Actions workflow and the entire
setup step is "install flox, activate". No apt-get, no setup-python, no cache
keys to tune.

## 20 · Terminal: the agent sandbox, by reference — 18:00 (≈200 words)

**[→]** One more variation, and this is the one that matters for agents.

This sandbox didn't clone anything. `flox activate -r` takes a reference to an
environment on FloxHub, pulls it, and runs the command inside it. Same
closure, same Python, now reporting `aarch64-linux`.

Redis says "down" here, and that's correct: I ran `activate` without `-s`, so
no services started. The app is honest about it.

This is the emulated one. To run it live, `flox push` from the repo first;
that needs a FloxHub account, which is the hosted part I mentioned.

Why does this matter for agents? Because the agent sandbox is the machine that
was set up with the least human judgement. If the only thing it has to know is
one reference string, there's nothing left to guess. It doesn't read your
README and pick a Python. It gets the Python.

And if you'd rather not depend on the hosted piece, the git clone path on the
previous slide gets the same result. The lock is in the repo.

## 21 · Section: Demo 3 — 19:30 (≈30 words)

That was problem one, build it the same everywhere. Now problem two: run it
the same wherever it lands next. The artifact, and the receipt.

## 22 · Terminal: flox build — 19:45 (≈180 words)

**[→]** `flox build`. Watch the first line: Nix sandbox, pure mode. The build
command from the manifest runs with no network and no access to the host. It
can see the tracked sources and the packages in the manifest. That's it.

Look at the output path it writes into. It's already a store path. The hash was
computed before the build ran.

And look at the interpreter line. The script started life with
`#!/usr/bin/env python3`. The build rewrote that to the exact Python from the
lock, by store path. So this artifact doesn't go looking for a Python on
whatever host it lands on. It brings its own.

**[→]** `readlink` on the result. It's a symlink into the store.

**[→]** Run it directly, outside the environment. It reports Python 3.14.7,
because it's wired to that Python, not to the host.

If you're a Nix person: this is a derivation, built by Nix, in the Nix
sandbox. You could write it as a `.nix` file instead. The manifest version is
three lines of shell and two settings.

## 23 · Terminal: containerize, and the receipt — 21:00 (≈220 words)

**[→]** `flox containerize`. One command, no Dockerfile. It turns the
environment's closure into an OCI image and hands it to Docker.

**[→]** Run the app inside the image. Same report. Python 3.14.7. The system
flipped to `aarch64-linux`, because the image is Linux. The environment path
is now a store path inside the image. Same lock, different machine, same
Python.

The image is the closure. It isn't "start from Debian and apt-get Python on
top". It's exactly the fifty-one paths from slide nine, plus Redis, plus the
app. Nothing else is in there to patch.

**[→]** And the receipt. This is a small Python script in the repo that reads
the lockfile and emits an SPDX software bill of materials. It lists four
packages with exact versions and licenses. Notice it's not scanning a
filesystem after the fact and guessing what it found. The lock is what went
in, so the SBOM is derived from the lock.

That's a thing you can only do because the lock is complete. And it's a plain
Python script; the lockfile is JSON, you can read it with jq, and you can
write your own tooling against it.

## 24 · One definition, shared — 22:30 (≈110 words)

Pulling it together. People and agents use the same file and the same verbs.

For a person: `flox init` once. `flox activate -s` every morning. `flox push`
if you want to share it by reference, or just commit the `.flox` directory if
you don't.

For an agent: there are open source skills, Apache-2, that teach it to write
the same manifest. It verifies with `flox activate -- <command>`, the same
form we used on three machines. And there are no ad hoc installs, because the
manifest is the only input.

The agent isn't a special case. It edits the same file and gets the same
closure.

## 25 · Terminal: an agent edits the environment — 23:15 (≈110 words)

**[→]** Here's what that looks like. I ask Claude Code to add Node 22 and
prove it activates.

It searches, it installs with a version constraint, it verifies with
`flox activate -- node --version`, and it reports the two lines it added to
the manifest and that the lock now resolves Node 22.21.1 on all three
systems.

This transcript is emulated. Every command in it is real and that version is
what the catalog resolves today. If you'd rather see it live, the skill is
installed in this environment's Claude Code, so you can run exactly that
prompt.

## 26 · Make everywhere mean the same thing — 24:00 (≈60 words)

Software is built everywhere now. By people, by CI, by images, by models. The
thing you can do about it is make "everywhere" mean the same thing: declare
the environment once, lock it, and reproduce it from the lock on every machine,
for every human and every agent.

## 27 · Thank you — 24:15 (≈100 words)

Links. If you want the engine, start with Nix and nixpkgs; everything in this
talk sits on them. The Flox CLI is on GitHub under GPL-2 if you want the TOML
path. The agent skills are Apache-2. And this repository has the demo app, the
manifest, the lock, the SBOM script, the CI workflow, and this deck, including
the plain-nix commands from the middle section so you can check the store
paths yourself.

Thanks. I'm happy to take questions, and I'm especially happy to take the
hard ones about where the hosted parts are and what happens without them.

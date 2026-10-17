export class ReplayController {
  constructor(onFrame) {
    this.onFrame = onFrame;
    this.frames = [];
    this.index = 0;
    this.timer = null;
    this.playing = false;

    this.controls = document.getElementById("replay-controls");
    this.slider = document.getElementById("replay-slider");
    this.playButton = document.getElementById("play");
    this.speed = document.getElementById("speed");

    const self = this;

    document.getElementById("previous").addEventListener("click", function () {
      self.pause();
      self.select(self.index - 1);
    });

    document.getElementById("next").addEventListener("click", function () {
      self.pause();
      self.select(self.index + 1);
    });

    this.slider.addEventListener("input", function () {
      self.pause();
      self.select(Number(self.slider.value));
    });

    this.playButton.addEventListener("click", function () {
      if (self.playing) {
        self.pause();
      } else {
        self.play();
      }
    });

    this.speed.addEventListener("change", function () {
      if (self.playing) {
        self.pause();
        self.play();
      }
    });
  }

  load(frames) {
    this.pause();
    this.frames = frames;
    this.index = 0;
    this.controls.disabled = frames.length === 0;
    this.slider.max = String(Math.max(0, frames.length - 1));
    this.slider.value = "0";

    if (frames.length > 0) {
      this.select(0);
    }
  }

  select(index) {
    if (this.frames.length === 0) {
      return;
    }

    this.index = Math.max(0, Math.min(index, this.frames.length - 1));
    this.slider.value = String(this.index);

    this.onFrame(
      this.frames[this.index],
      this.index > 0 ? this.frames[this.index - 1] : null
    );
  }

  play() {
    if (this.frames.length < 2) {
      return;
    }

    if (this.index === this.frames.length - 1) {
      this.select(0);
    }

    this.playing = true;
    this.playButton.textContent = "Pause";
    this.schedule();
  }

  schedule() {
    const self = this;

    this.timer = window.setTimeout(function () {
      if (!self.playing) {
        return;
      }

      self.select(self.index + 1);

      if (self.index === self.frames.length - 1) {
        self.pause();
      } else {
        self.schedule();
      }
    }, Number(this.speed.value));
  }

  pause() {
    window.clearTimeout(this.timer);
    this.timer = null;
    this.playing = false;
    this.playButton.textContent = "Play";
  }
}
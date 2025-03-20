import { defineStore } from 'pinia';
import { ref } from 'vue';

const urlCreator = window.URL || window.webkitURL;

export const useCanvasStore = defineStore('canvas', () => {
  const canvasSize = ref({ width: 0, height: 0 });
  const selectedMode = ref('draw');
  const selectedSize = ref(3);
  const penColour = ref('black');
  const penFill = ref();
  const hideCanvas = ref(false);
  const pauseDraw = ref(false);
  const isDrawing = ref(false);
  const immediateResize = ref(false);

  function updateCanvasSize(width, height) {
    canvasSize.value = { width, height };
  }

  function canvasLoadImage({ ctx, blob, url, width, height, cb, maintainRatio = true }) {
    const img = new Image();
    width ??= canvasSize.value.width;
    height ??= canvasSize.value.height;

    img.onload = function () {
      if (maintainRatio) {
        const scale = Math.min(width / img.width, height / img.height);
        ctx.scale(scale, scale);
      } else {
        ctx.scale(width / img.width, height / img.height);
      }

      ctx.drawImage(img, 0, 0);
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      cb?.();
    };

    if (url) img.src = url;
    else if (blob) img.src = urlCreator.createObjectURL(blob);
    else cb?.();
  }

  function setPenMode(mode) {
    selectedMode.value = mode;
  }

  function setPenSize(size) {
    selectedSize.value = size;
  }

  function setPenColour(colour) {
    penColour.value = colour;
  }

  function setPenFill(fill) {
    penFill.value = !!fill;
  }

  function setIsDrawing(drawing) {
    isDrawing.value = !!drawing;
  }

  function sethideCanvas(hide) {
    hideCanvas.value = !!hide;
  }

  function setPauseDraw(pause) {
    pauseDraw.value = !!pause;
  }

  return {
    canvasSize,
    selectedMode,
    selectedSize,
    penColour,
    penFill,
    isDrawing,
    hideCanvas,
    pauseDraw,
    immediateResize,
    updateCanvasSize,
    canvasLoadImage,
    setPenMode,
    setPenSize,
    setPenColour,
    setPenFill,
    sethideCanvas,
    setPauseDraw,
    setIsDrawing,
  };
});

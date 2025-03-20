<script setup>
import { vElementSize } from '@vueuse/components';
import { ref, watch, defineExpose } from 'vue';
import { storeToRefs } from 'pinia';
import { useProjectStore } from '@/stores/project';
import { useCanvasStore } from '@/stores/canvas';

const projectStore = useProjectStore();
const { images, sketches, selectedUuid } = storeToRefs(projectStore);
const { saveSketch } = projectStore;

const canvasStore = useCanvasStore();
const {
  selectedMode,
  selectedSize,
  penColour,
  penFill,
  isDrawing,
  hideCanvas,
  pauseDraw,
  immediateResize,
} = storeToRefs(canvasStore)
const { updateCanvasSize, canvasLoadImage } = canvasStore;

const CIRCLE = 2 * Math.PI;

const canvas = ref();
const sketchCanvas = ref();

let resizeDebounce;
let curX;
let curY;
let anchorX;
let anchorY;

function getCtx() {
  return canvas.value.getContext('2d');
}

function getCtxSketch() {
  return sketchCanvas.value.getContext('2d');
}

function onResize({ width, height }) {
  if (resizeDebounce) {
    clearTimeout(resizeDebounce);
    resizeDebounce = null;
  }

  resizeDebounce = setTimeout(() => {
    const oriWidth = canvas.value?.width;
    const oriHeight = canvas.value?.height;

    width = Math.floor(width);
    height = Math.floor(height);
    if (oriWidth === width && oriHeight === height) return;
    if (!width || !height) return;

    const ctx = getCtx();
    const scale = width / oriWidth;

    canvas.value.toBlob((blob) => {
      createImageBitmap(blob).then((imageBitmap) => {
        canvas.value.width = width;
        canvas.value.height = height;
        sketchCanvas.value.width = width;
        sketchCanvas.value.height = height;

        ctx.scale(scale, scale);
        ctx.drawImage(imageBitmap, 0, 0);
        ctx.setTransform(1, 0, 0, 1, 0, 0);

        resizeDebounce = null;
      });
    });

    updateCanvasSize(width, height);
  }, immediateResize.value ? 0 : 500);

  immediateResize.value = false;
}

function saveCanvas() {
  canvas.value.toBlob((blob) => saveSketch(blob, selectedUuid.value));
}

function canvasClear() {
  getCtx().clearRect(0, 0, canvas.value.width, canvas.value.height);
}

function sketchClear() {
  getCtxSketch().clearRect(0, 0, sketchCanvas.value.width, sketchCanvas.value.height);
}

function drawShape({ ctx, stroke = true, size, fill }) {
  if (stroke) {
    ctx.lineWidth = size;
    ctx.strokeStyle = penColour.value;
    ctx.stroke();
  }
  if (fill) {
    ctx.fillStyle = penColour.value;
    ctx.fill();
  }
}

function drawLine({ ctx, x, y, size, fromX, fromY, clear = false }) {
  if (fromX !== undefined && fromY !== undefined) ctx.moveTo(fromX, fromY);
  if (!clear) ctx.strokeStyle = penColour.value;

  ctx.lineTo(x, y);
  ctx.lineWidth = size;
  ctx.stroke();
}

function drawOval({ ctx, x, y, radiusX, radiusY, stroke = true, size, fill }) {
  ctx.beginPath();
  ctx.ellipse(x, y, radiusX, radiusY, 0, 0, CIRCLE);
  drawShape({ ctx, stroke, size, fill });
  ctx.closePath();
}

function drawRect({ ctx, x, y, width, height, stroke = true, size, fill }) {
  ctx.beginPath();
  ctx.rect(x, y, width, height);
  drawShape({ ctx, stroke, size, fill });
  ctx.closePath();
}

function clearRect({ ctx, x, y, size }) {
  ctx.clearRect(x, y, size, size);
}

function getLocation(event) {
  const location = canvas.value.getBoundingClientRect();
  curX = event.clientX - location.left;
  curY = event.clientY - location.top;
  return { curX, curY };
}

function canvasMouseDown(event) {
  if (!images.value.has(selectedUuid.value)) return;
  if (pauseDraw.value) return;
  isDrawing.value = true;

  const { curX, curY } = getLocation(event);
  const size = selectedSize.value;
  const ctx = getCtx();
  ctx.globalCompositeOperation = 'source-over';

  const x = curX - size / 2;
  const y = curY - size / 2;

  switch (selectedMode.value) {
    case 'draw':
      drawRect({ ctx, x, y, width: size, height: size, fill: true, stroke: false });
      ctx.beginPath();
      ctx.moveTo(curX, curY);
      break;

    case 'erase':
      clearRect({ ctx, x, y, size });
      ctx.beginPath();
      ctx.globalCompositeOperation = 'destination-out';
      ctx.moveTo(curX, curY);
      break;

    case 'line':
    case 'rectangle':
    case 'oval':
      anchorX = curX;
      anchorY = curY;
      break;
  }
}

function canvasMouseEnd(event) {
  if (!isDrawing.value) return;

  const { curX: x, curY: y } = getLocation(event);
  const size = selectedSize.value;
  const ctx = getCtx();
  sketchClear();

  switch (selectedMode.value) {
    case 'draw':
      ctx.closePath();
      break;

    case 'line':
      ctx.beginPath();
      drawLine({ ctx, x, y, size, fromX: anchorX, fromY: anchorY });
      ctx.closePath();
      break;

    case 'rectangle':
      drawRect({
        ctx,
        x: Math.min(anchorX, x),
        y: Math.min(anchorY, y),
        width: Math.abs(x - anchorX),
        height: Math.abs(y - anchorY),
        size,
        fill: penFill.value,
      });
      break;

    case 'oval':
      drawOval({
        ctx,
        x: (anchorX + x) / 2,
        y: (anchorY + y) / 2,
        radiusX: Math.abs(x - anchorX) / 2,
        radiusY: Math.abs(y - anchorY) / 2,
        size,
        fill: penFill.value,
      });
      break;
  }

  anchorX = null;
  anchorY = null;

  isDrawing.value = false;
  saveCanvas();
}

function canvasMouseLeave() {
  if (!isDrawing.value) sketchClear()
}

function canvasMouseMove(event) {
  if (!selectedUuid.value) return;

  const { curX: x, curY: y } = getLocation(event);
  const size = selectedSize.value;
  const ctx = getCtx();
  const ctxSketch = getCtxSketch();

  sketchClear();
  if (!isDrawing.value) {
    drawRect({
      ctx: ctxSketch,
      x: curX - size / 2,
      y: curY - size / 2,
      width: size,
      height: size,
      fill: true,
      stroke: false,
    });
    return;
  }

  switch (selectedMode.value) {
    case 'draw':
      drawLine({ ctx, x, y, size });
      break;

    case 'erase':
      drawLine({ ctx, x, y, size, clear: true });
      break;

    case 'line':
      if (anchorX === null || anchorY === null) break;
      ctxSketch.beginPath();
      drawLine({ ctx: ctxSketch, x, y, size, fromX: anchorX, fromY: anchorY });
      ctxSketch.closePath();
      break;

    case 'rectangle':
      if (anchorX === null || anchorY === null) break;
      drawRect({
        ctx: ctxSketch,
        x: Math.min(anchorX, x),
        y: Math.min(anchorY, y),
        width: Math.abs(x - anchorX),
        height: Math.abs(y - anchorY),
        size,
        fill: penFill.value,
      });
      break;

    case 'oval':
      if (anchorX === null || anchorY === null) break;
      drawOval({
        ctx: ctxSketch,
        x: (anchorX + x) / 2,
        y: (anchorY + y) / 2,
        radiusX: Math.abs(x - anchorX) / 2,
        radiusY: Math.abs(y - anchorY) / 2,
        size,
        fill: penFill.value,
      });
      break;
  }
}

function resetCanvas() {
  const url = sketches.value.get(selectedUuid.value)?.url;
  if (url) canvasLoadImage({ ctx: getCtx(), url });
}

function loadImage(url) {
  canvasClear();
  canvasLoadImage({ ctx: getCtx(), url })
}

watch(
  [selectedUuid, sketches],
  (newValue, oldValue) => {
    const url = sketches.value.get(newValue[0])?.url;
    if (!url) {
      canvasClear();
    } else if (oldValue[0] !== newValue[0]) {
      loadImage(url)
    }
  },
  { deep: true },
);

defineExpose({ canvasMouseEnd, canvasClear, saveCanvas, resetCanvas, loadImage })
</script>

<template>
  <div v-show="!hideCanvas" class="absolute w-full h-full p-1 pb-0 flex justify-center bg-white overflow-auto">
    <div class="relative w-full min-h-full h-fit pb-1">
      <img v-show="images.get(selectedUuid)?.url" :src="images.get(selectedUuid)?.url" class="w-full border-2 border-gray-400 pointer-events-none select-none" />

      <div
        v-element-size="onResize"
        class="absolute top-0 z-10 w-full h-[calc(100%-var(--spacing))] border-2"
        :class="{ 'cursor-crosshair': images.has(selectedUuid) && !pauseDraw }"
      >
        <canvas
          ref="canvas"
          @mousedown="canvasMouseDown"
          @mouseup="canvasMouseEnd"
          @mousemove="canvasMouseMove"
          @mouseleave="canvasMouseLeave"
          class="w-full h-full"
          :class="{ 'pointer-events-none': pauseDraw }"
        ></canvas>
        <canvas ref="sketchCanvas" class="absolute top-0 left-0 w-full h-full pointer-events-none"></canvas>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CanvasBoard',
  data() {
    return {};
  },
};
</script>

<script setup>
import { ref } from 'vue';
import { storeToRefs } from 'pinia';
import { useProjectStore } from '@/stores/project';
import { useCanvasStore } from '@/stores/canvas';
import PencilIcon from './icons/PencilIcon.vue';
import EraserIcon from './icons/EraserIcon.vue';
import TrashIcon from './icons/TrashIcon.vue';
import ClearImageIcon from './icons/ClearImageIcon.vue';
import AddImageIcon from './icons/AddImageIcon.vue';
import LineIcon from './icons/LineIcon.vue';
import RectangleIcon from './icons/RectangleIcon.vue';
import OvalIcon from './icons/OvalIcon.vue';
import DotIcon from './icons/DotIcon.vue';
import UndoIcon from './icons/UndoIcon.vue';
import RedoIcon from './icons/RedoIcon.vue';
import SliderSwitch from './SliderSwitch.vue';

const projectStore = useProjectStore();
const {
  images,
  undoStacks,
  redoStacks,
  selectedUuid
} = storeToRefs(projectStore);
const {
  updateImage,
  clearImage,
} = projectStore;

const canvasStore = useCanvasStore();
const { selectedMode, selectedSize, penFill, penColour } = storeToRefs(canvasStore)
const { setPauseDraw } = canvasStore;

const PEN_MODES = [
  { mode: 'draw', icon: PencilIcon },
  { mode: 'erase', icon: EraserIcon },
  { mode: 'line', icon: LineIcon },
  { mode: 'rectangle', icon: RectangleIcon },
  { mode: 'oval', icon: OvalIcon },
];
const PEN_SIZES = [2, 3, 5, 7, 9];

const btnFileAdd = ref();

function addImage() {
  btnFileAdd.value.click();
}

function onAddImage(event) {
  for (const file of event.currentTarget.files) {
    updateImage(file, selectedUuid.value)
    break;
  }
  btnFileAdd.value.value = null;
}
</script>

<template>
  <div class="absolute w-0 h-0 max-w-0 max-h-0" :class="{ hidden: !images.has(selectedUuid) }">
    <div class="relative">
      <div class="absolute right-0 flex bg-white border-x-4 border-r-cyan-800 select-none">
        <div class="flex flex-col border-r-2 border-y-4">
          <button
            v-for="size of PEN_SIZES"
            :key="size"
            @click="selectedSize = size"
            class="w-10 h-10 flex justify-center items-center cursor-pointer hover:brightness-90 active:brightness-80"
            :class="selectedSize === size ? 'bg-slate-300' : 'bg-white'"
          >
            <DotIcon :width="size" :height="size" />
          </button>

          <div class="mt-2.75 flex flex-col gap-5 justify-center items-center">
            <SliderSwitch @triggered="(event) => (penFill = event.currentTarget.checked)" />

            <label class="mb-3">
              <div class="w-4 h-4 border-2 cursor-pointer" :style="{ background: penFill ? penColour : 'transparent', 'border-color': penColour }"></div>
              <input
                type="color"
                class="absolute w-0 h-0"
                @focus="() => setPauseDraw(true)"
                @blur="() => setPauseDraw(false)"
                @change="(event) => (penColour = event.currentTarget.value)"
              />
            </label>
          </div>
        </div>

        <div class="flex flex-col border-y-4">
          <button
            v-for="mode of PEN_MODES"
            :key="mode.mode"
            @click="selectedMode = mode.mode"
            class="w-10 h-10 flex justify-center items-center cursor-pointer hover:brightness-90 active:brightness-80"
            :class="{ 'bg-slate-300': selectedMode === mode.mode, 'bg-white': selectedMode !== mode.mode }"
          >
            <component :is="mode.icon" width="30" height="30" />
          </button>

          <button
            @click="$emit('onClearCanvas')"
            class="w-10 h-10 flex justify-center items-center cursor-pointer bg-white hover:brightness-90 active:brightness-80"
          >
            <TrashIcon width="30" height="30" />
          </button>

          <button @click="addImage" class="w-10 h-10 flex justify-center items-center cursor-pointer bg-white hover:brightness-90 active:brightness-80">
            <AddImageIcon width="30" height="30" />
            <input @change="onAddImage" type="file" class="hidden" ref="btnFileAdd" accept=".jpg,.png" />
          </button>

          <button @click="clearImage(selectedUuid)" class="w-10 h-10 flex justify-center items-center cursor-pointer bg-white hover:brightness-90 active:brightness-80">
            <ClearImageIcon width="30" height="30" />
          </button>

          <hr class="border-1" />

          <button
            @click="$emit('undo')"
            :disabled="!undoStacks.get(selectedUuid)?.length"
            class="flex justify-center items-center p-2 enabled:cursor-pointer bg-white enabled:hover:brightness-90 enabled:active:brightness-80"
          >
            <UndoIcon width="24" height="24" class="pointer-events-none" :class="{ 'opacity-50': !undoStacks.get(selectedUuid)?.length }" />
          </button>

          <button
            @click="$emit('redo')"
            :disabled="!redoStacks.get(selectedUuid)?.length"
            class="flex justify-center items-center p-2 enabled:cursor-pointer bg-white enabled:hover:brightness-90 enabled:active:brightness-80"
          >
            <RedoIcon width="24" height="24" class="pointer-events-none" :class="{ 'opacity-50': !redoStacks.get(selectedUuid)?.length }" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PenSelectors',
  data() {
    return {};
  },
};
</script>

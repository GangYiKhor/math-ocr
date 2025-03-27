<script setup>
import UploadIcon from './icons/UploadIcon.vue';
import { storeToRefs } from 'pinia';
import { useProjectStore } from '@/stores/project';
import { ref } from 'vue';
import { useCanvasStore } from '@/stores/canvas';

const props = defineProps(['MAX_FILE_SIZE']);
const MAX_FILE_SIZE = props.MAX_FILE_SIZE ?? 50;

const projectStore = useProjectStore();
const { images, sketches, selectedUuid } = storeToRefs(projectStore);
const { selectFile, removeFile, loadFiles, emptyFile } = projectStore;

const canvasStore = useCanvasStore();
const { immediateResize } = storeToRefs(canvasStore);

const btnFileUpload = ref();

function uploadFile() {
  btnFileUpload.value.click();
}

function onUploadFile(event) {
  loadFiles(event.currentTarget.files);
  btnFileUpload.value.value = null;
}
</script>

<template>
  <div class="relative h-30 w-full px-0.5 overflow-x-auto overflow-y-hidden scroll-smooth text-nowrap horizontal-custom-scrollbar select-none">
    <div v-for="item of images.entries()" :key="item[0]" class="relative h-full w-20 p-1 inline-block">
      <div
        @click="() => { selectFile(item[0]); immediateResize = true; }"
        class="relative h-full w-full border-2 rounded-sm bg-gray-200 cursor-pointer hover:brightness-90 active:brightness-80"
      >
        <img v-show="item[1]" :src="item[1]?.url" class="h-full w-full rounded-sm object-contain object-left-top pointer-events-none select-none" />
        <img
          v-show="sketches.get(item[0])"
          :src="sketches.get(item[0])?.url"
          class="absolute top-0 left-0 h-full w-full rounded-sm object-contain object-left-top pointer-events-none select-none"
        />
        <div class="absolute top-0 left-0 h-full w-full rounded-sm opacity-30" :class="{'bg-blue-200': item[0] === selectedUuid}"></div>
      </div>

      <button
        @click="removeFile(item[0])"
        class="absolute z-10 right-0 top-0 px-1.5 pb-1 text-xs text-red-500 font-bold bg-red-100 border-2 border-red-500 rounded-full cursor-pointer hover:bg-red-200 active:bg-red-300 transition-colors select-none"
      >
        x
      </button>
    </div>

    <div class="h-full w-20 p-1 inline-block">
      <div
        v-if="images.size < MAX_FILE_SIZE"
        @click="uploadFile"
        class="relative h-full w-full border-2 rounded-sm cursor-pointer hover:bg-neutral-200 active:bg-neutral-300 select-none"
      >
        <div class="absolute w-full h-full flex justify-center items-center">
          <UploadIcon width="30" height="30" />
        </div>
      </div>
    </div>

    <div class="h-full w-20 p-1 inline-block">
      <div
        v-if="images.size < MAX_FILE_SIZE"
        @click="emptyFile"
        class="relative h-full w-full border-2 rounded-sm cursor-pointer hover:bg-neutral-200 active:bg-neutral-300 select-none"
      >
        <span class="absolute top-1/4 left-1/4 w-1/2 h-1/2 flex justify-center items-center font-bold text-2xl">+</span>
      </div>
    </div>

    <input @change="onUploadFile" type="file" class="hidden" ref="btnFileUpload" accept=".jpg,.png" multiple />
  </div>
</template>

<script>
export default {
  name: 'FileList',
  data() {
    return {};
  },
};
</script>

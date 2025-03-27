<script setup>
const urlCreator = window.URL || window.webkitURL;

const props = defineProps(['id', 'title', 'vertical']);
const url = urlCreator.createObjectURL(new Blob([new ArrayBuffer(0)]));
let uuid = url.split('/').at(-1);
const id = props?.id ?? `slider-${uuid}`;
</script>

<template>
  <div class="flex items-center" :class="{'flex-col justify-center': !!props?.vertical, 'gap-1': !props?.vertical}">
    <label class="switch">
      <input :id="id" @click="(event) => $emit('triggered', event)" type="checkbox" />
      <span class="slider round"></span>
    </label>
    <label v-if="!!props?.title" :for="id">{{ props.title }}</label>
  </div>
</template>

<script>
export default {
  name: 'SliderSwitch',
  data() {
    return {};
  },
};
</script>

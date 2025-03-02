<script setup>
import { defineProps } from 'vue';

const props = defineProps(['width', 'height']);
</script>

<template>
  <svg :width="`${props.width ?? 50}px`" :height="`${props.height ?? 50}px`" viewBox="0 0 512 512">
    <line x1="0" y1="512" x2="256" y2="0" style="stroke: black; stroke-width: 50" />
    <line x1="256" y1="0" x2="512" y2="512" style="stroke: black; stroke-width: 50" />
    <line x1="0" y1="512" x2="512" y2="512" style="stroke: black; stroke-width: 100" />
  </svg>
</template>

<script>
export default {
  name: 'TriangleIcon',
  data() {
    return {};
  },
};
</script>

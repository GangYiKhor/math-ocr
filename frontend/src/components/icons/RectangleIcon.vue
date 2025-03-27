<script setup>
const props = defineProps(['width', 'height']);
</script>

<template>
  <svg :width="`${props.width ?? 50}px`" :height="`${props.height ?? 50}px`" viewBox="0 0 512 512">
    <rect width="512" height="512" style="fill: none; stroke: black; stroke-width: 100" />
  </svg>
</template>

<script>
export default {
  name: 'RectangleIcon',
  data() {
    return {};
  },
};
</script>

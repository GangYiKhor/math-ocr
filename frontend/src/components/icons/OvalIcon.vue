<script setup>
const props = defineProps(['width', 'height']);
</script>

<template>
  <svg :width="`${props.width ?? 50}px`" :height="`${props.height ?? 50}px`" viewBox="0 0 512 512">
    <circle cx="256" cy="256" r="230" style="fill: none; stroke: black; stroke-width: 50" />
  </svg>
</template>

<script>
export default {
  name: 'OvalIcon',
  data() {
    return {};
  },
};
</script>

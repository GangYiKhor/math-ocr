<script setup>
import { defineProps } from 'vue';

const props = defineProps(['width', 'height', 'colour']);
</script>

<template>
  <svg :width="`${props.width ?? 50}px`" :height="`${props.height ?? 50}px`" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <g clip-path="url(#clip0_429_11155)">
      <path d="M16 3H4V16" :stroke="props.colour ?? 'white'" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" />
      <path
        d="M8 7H20V19C20 20.1046 19.1046 21 18 21H10C8.89543 21 8 20.1046 8 19V7Z"
        :stroke="props.colour ?? 'black'"
        stroke-width="2.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </g>
    <defs>
      <clipPath id="clip0_429_11155">
        <rect width="24" height="24" :fill="props.colour ?? 'black'" />
      </clipPath>
    </defs>
  </svg>
</template>

<script>
export default {
  name: 'CopyIcon',
  data() {
    return {};
  },
};
</script>

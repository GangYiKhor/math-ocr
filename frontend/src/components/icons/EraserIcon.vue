<script setup>
const props = defineProps(['width', 'height']);
</script>

<template>
  <svg :width="`${props.width ?? 50}px`" :height="`${props.height ?? 50}px`" viewBox="0 -1.65 96.313 96.313" xmlns="http://www.w3.org/2000/svg">
    <g id="eraser" transform="translate(-656.357 -408.933)">
      <g id="Group_19" data-name="Group 19">
        <path
          id="Path_57"
          data-name="Path 57"
          d="M657.917,461.343a4.59,4.59,0,0,0-.437,6.456l28.466,32.581a4.587,4.587,0,0,0,6.456.436l58.705-51.285a4.588,4.588,0,0,0,.439-6.456L723.08,410.491a4.59,4.59,0,0,0-6.456-.433Z"
          fill="#f53b33"
        />
      </g>
      <g id="Group_21" data-name="Group 21">
        <g id="Group_20" data-name="Group 20">
          <path
            id="Path_58"
            data-name="Path 58"
            d="M657.917,461.343a4.59,4.59,0,0,0-.437,6.456l28.466,32.581a4.587,4.587,0,0,0,6.456.436l58.705-51.285a4.588,4.588,0,0,0,.439-6.456L723.08,410.491a4.59,4.59,0,0,0-6.456-.433Z"
            fill="#f27a74"
          />
        </g>
      </g>
      <path
        id="Path_59"
        data-name="Path 59"
        d="M751.546,443.075,723.08,410.491a4.59,4.59,0,0,0-6.456-.433l-1.148,1,34.487,39.473,1.144-1A4.588,4.588,0,0,0,751.546,443.075Z"
        fill="#f55162"
      />
      <path id="Path_60" data-name="Path 60" d="M687.27,435.7l-29.353,25.644a4.59,4.59,0,0,0-.437,6.456l28.466,32.581a4.587,4.587,0,0,0,6.456.436l29.354-25.641Z" fill="#4d98d5" />
      <path
        id="Path_61"
        data-name="Path 61"
        d="M657.48,467.8l28.466,32.581a4.587,4.587,0,0,0,6.456.436l1.149-1-34.486-39.474-1.148,1A4.59,4.59,0,0,0,657.48,467.8Z"
        fill="#3387c1"
      />
      <g id="Group_23" data-name="Group 23">
        <g id="Group_22" data-name="Group 22">
          <path
            id="Path_62"
            data-name="Path 62"
            d="M679.243,451.995a1.144,1.144,0,0,1-.106,1.608l-11.683,10.205a1.142,1.142,0,0,1-1.61-.111h0a1.137,1.137,0,0,1,.109-1.607l11.68-10.2a1.142,1.142,0,0,1,1.61.11Z"
            fill="#a4c9d4"
          />
          <path
            id="Path_63"
            data-name="Path 63"
            d="M689.661,442.89a1.143,1.143,0,0,0-1.609-.11l-6.224,5.441a1.14,1.14,0,0,0,1.5,1.719l6.229-5.439A1.144,1.144,0,0,0,689.661,442.89Z"
            fill="#a4c9d4"
          />
        </g>
      </g>
    </g>
  </svg>
</template>

<script>
export default {
  name: 'EraserIcon',
  data() {
    return {};
  },
};
</script>

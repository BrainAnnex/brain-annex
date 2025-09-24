import multiselectMixin from './multiselectMixin.js';
import pointerMixin from './pointerMixin.js';


Vue.component('vue-multiselect',
    {
        name: 'vue-multiselect',

        mixins: [multiselectMixin, pointerMixin],

        props: {
            data_from_flask : Array,

            /**
            * name attribute to match optional label element
            * @default ''
            * @type {String}
            */
            name: {
                type: String,
                default: ''
            },

            /**
            * String to show when pointing to an option
            * @default 'Press enter to select'
            * @type {String}
            */
            selectLabel: {
                type: String,
                default: 'Press enter to select'
            },

            /**
            * String to show next to selected option
            * @default 'Selected'
            * @type {String}
            */
            selectedLabel: {
                type: String,
                default: 'Selected'
            },

            /**
            * String to show when pointing to an alredy selected option
            * @default 'Press enter to remove'
            * @type {String}
            */
            deselectLabel: {
                type: String,
                default: 'Press enter to remove'
            },

            /**
            * Decide whether to show pointer labels
            * @default true
            * @type {Boolean}
            */
            showLabels: {
                type: Boolean,
                default: true
            },

            /**
            * Limit the display of selected options. The rest will be hidden within the limitText string.
            * @default 99999
            * @type {Integer}
            */
            limit: {
                type: Number,
                default: 99999
            },

            /**
            * Sets maxHeight style value of the dropdown
            * @default 300
            * @type {Integer}
            */
            maxHeight: {
                type: Number,
                default: 300
            },

            /**
            * Function that process the message shown when selected
            * elements pass the defined limit.
            * @default 'and * more'
            * @param {Int} count Number of elements more than limit
            * @type {Function}
            */
            limitText: {
                type: Function,
                default: count => `and ${count} more`
            },

            /**
            * Set true to trigger the loading spinner.
            * @default False
            * @type {Boolean}
            */
            loading: {
                type: Boolean,
                default: false
            },

            /**
            * Disables the multiselect if true.
            * @default false
            * @type {Boolean}
            */
            disabled: {
                type: Boolean,
                default: false
            },

            /**
            * Fixed opening direction
            * @default ''
            * @type {String}
            */
            openDirection: {
                type: String,
                default: ''
            },

            showNoResults: {
                type: Boolean,
                default: true
            },

            tabindex: {
                type: Number,
                default: 0
            }

        }, // END props


        // TEMPLATE
        template: `
            <div
                :tabindex="searchable ? -1 : tabindex"
                :class="{ 'multiselect--active': isOpen, 'multiselect--disabled': disabled, 'multiselect--above': isAbove }"
                @focus="activate()"
                @blur="searchable ? false : deactivate()"
                @keydown.self.down.prevent="pointerForward()"
                @keydown.self.up.prevent="pointerBackward()"
                @keydown.enter.tab.stop.self="addPointerElement($event)"
                @keyup.esc="deactivate()"
                class="multiselect">
                  <slot name="caret" :toggle="toggle">
                    <div @mousedown.prevent.stop="toggle()" class="multiselect__select"></div>
                  </slot>
                  <slot name="clear" :search="search"></slot>
                  <div ref="tags" class="multiselect__tags" :class="inputContainerClass">
                    <div class="multiselect__tags-wrap" v-show="visibleValue.length > 0">
                      <template v-for="option of visibleValue" @mousedown.prevent>
                        <slot name="tag" :option="option" :search="search" :remove="removeElement">
                          <span class="multiselect__tag">
                            <span v-text="getOptionLabel(option)"></span>
                            <i aria-hidden="true" tabindex="1" @keydown.enter.prevent="removeElement(option)"  @mousedown.prevent="removeElement(option)" class="multiselect__tag-icon"></i>
                          </span>
                        </slot>
                      </template>
                    </div>
                    <template v-if="internalValue && internalValue.length > limit">
                      <strong class="multiselect__strong" v-text="limitText(internalValue.length - limit)"></strong>
                    </template>
                    <transition name="multiselect__loading">
                      <slot name="loading"><div v-show="loading" class="multiselect__spinner"></div></slot>
                    </transition>
                    <input
                      ref="search"
                      :name="name"
                      :id="id"
                      type="text"
                      autocomplete="off"
                      :placeholder="placeholder"
                      v-if="searchable"
                      :style="inputStyle"
                      :value="isOpen ? search : currentOptionLabel"
                      :disabled="disabled"
                      :tabindex="tabindex"
                      @input="updateSearch($event.target.value)"
                      @focus.prevent="activate()"
                      @blur.prevent="deactivate()"
                      @keyup.esc="deactivate()"
                      @keydown.down.prevent="pointerForward()"
                      @keydown.up.prevent="pointerBackward()"
                      @keydown.enter.prevent.stop.self="addPointerElement($event)"
                      @keydown.delete.stop="removeLastElement()"
                      class="multiselect__input"
                      :class="inputClass"/>
                    <span
                      v-if="!searchable"
                      class="multiselect__single"
                      @mousedown.prevent="toggle"
                      v-text="currentOptionLabel">
                    </span>
                  </div>
                  <transition name="multiselect">
                    <div
                      class="multiselect__content-wrapper"
                      v-show="isOpen"
                      @focus="activate"
                      @mousedown.prevent
                      :style="{ maxHeight: optimizedHeight + 'px' }"
                      ref="list">
                      <ul class="multiselect__content" :style="contentStyle">
                        <slot name="beforeList"></slot>
                        <li v-if="multiple && max === internalValue.length">
                          <span class="multiselect__option">
                            <slot name="maxElements">Maximum of {{ max }} options selected. First remove a selected option to select another.</slot>
                          </span>
                        </li>
                        <template v-if="!max || internalValue.length < max">
                          <li class="multiselect__element" v-for="(option, index) of filteredOptions" :key="index">
                            <span
                              v-if="!(option && (option.$isLabel || option.$isDisabled))"
                              :class="optionHighlight(index, option)"
                              @click.stop="select(option)"
                              @touchstart.stop.prevent="handleTouchStartStop(index, option)"
                              @mouseenter.self="pointerSet(index)"
                              :data-select="option && option.isTag ? tagPlaceholder : selectLabelText"
                              :data-selected="selectedLabelText"
                              :data-deselect="deselectLabelText"
                              class="multiselect__option">
                                <slot name="option" :option="option" :search="search">
                                  <span>{{ getOptionLabel(option) }}</span>
                                </slot>
                            </span>
                            <span
                              v-if="option && (option.$isLabel || option.$isDisabled)"
                              :class="optionHighlight(index, option)"
                              class="multiselect__option multiselect__option--disabled">
                                <slot name="option" :option="option" :search="search">
                                  <span>{{ getOptionLabel(option) }}</span>
                                </slot>
                            </span>
                          </li>
                        </template>
                        <li v-show="showNoResults && (filteredOptions.length === 0 && search && !loading)">
                          <span class="multiselect__option">
                            <slot name="noResult">No elements found. Consider changing the search query.</slot>
                          </span>
                        </li>
                        <slot name="afterList"></slot>
                      </ul>
                    </div>
                  </transition>
              </div>
            `,  // END template


        // COMPUTED
        computed: {
            visibleValue () {
                return this.multiple
                  ? this.internalValue.slice(0, this.limit)
                  : []
            },

            deselectLabelText () {
                return this.showLabels
                  ? this.deselectLabel
                  : ''
            },

            selectLabelText () {
                return this.showLabels
                  ? this.selectLabel
                  : ''
            },

            selectedLabelText () {
                return this.showLabels
                  ? this.selectedLabel
                  : ''
            },

            inputStyle () {
                if (this.multiple && this.value && this.value.length) {
                  // Hide input by setting the width to 0 allowing it to receive focus
                  return this.isOpen ? { 'width': 'auto' } : { 'width': '0', 'position': 'absolute' }
                }
            },

            contentStyle () {
                return this.options.length
                  ? { 'display': 'inline-block' }
                  : { 'display': 'block' }
            },

            isAbove () {
                if (this.openDirection === 'above' || this.openDirection === 'top') {
                  return true
                } else if (this.openDirection === 'below' || this.openDirection === 'bottom') {
                  return false
                } else {
                  return this.prefferedOpenDirection === 'above'
                }
            }

        }  // END computed

    }
);  // end component 'multiselect'
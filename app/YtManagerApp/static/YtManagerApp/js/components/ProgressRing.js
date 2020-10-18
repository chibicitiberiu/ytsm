export class ProgressRing
{
    wrapperElement = null;
    svgElement = null;
    circleElement = null;

    constructor(wrapperElement) {
        this.wrapperElement = wrapperElement;
        this.buildDom();
    }

    buildDom() {
        let bounds = this.wrapperElement.getBoundingClientRect();
        this.svgElement = $(`<svg class="progress-ring" style="width: 100%; height: 100%;"></svg>`);
        this.svgElement.appendTo(this.wrapperElement);
        this.circleElement = $(`<circle fill="transparent"></circle>`);
        this.circleElement.appendTo(this.svgElement);

        let strokeColor = this.wrapperElement.data('stroke');
        if (strokeColor === undefined) {
            strokeColor = 'black';
        }
        this.circleElement.attr('stroke', strokeColor);

        let strokeWidth = this.wrapperElement.data('stroke-width');
        if (strokeWidth === undefined) {
            strokeWidth = '0.2em';
        }
        this.circleElement.attr('stroke-width', strokeWidth);

        let radius = Math.min(bounds.width, bounds.height) / 2;
    }
}
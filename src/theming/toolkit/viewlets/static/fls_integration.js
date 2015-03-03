/*
* Integration / Improvements for propertyshelfs FeaturedListingSlider 
*/

function resize2pixel(element, mode){
    /* check the width of the given element and set it explicit as static px
     *  mode = width (reset the width of element in px)
     *         height (resize the height of element)
     *         default (resize width& height of the element in px)
    */
    switch(mode){
        case 'width':
            $(element).width($(element).width());
            break;
        case 'height':
            $(element).height($(element).height());
            break;
        default:
        // re-set width & height
            $(element).width($(element).width());
            $(element).height($(element).height());
            break;
    }

}

function PSScaleSlider(obj) {
    console.log('responsive Slider Rasta');
    console.log(obj);
    var parentWidth = $('.ps_slider_wrapper').parent().width();
    console.log(parentWidth);

    

    if (parentWidth){
        try{
            obj.$ScaleWidth(parentWidth);
        }
        catch(error){
            console.log(error);
        }
    }
    //else
        //obj.setTimeout(PSScaleSlider(obj), 30);

    $(window).bind("resize", PSScaleSlider(obj));
    $(window).bind("orientationchange", PSScaleSlider(obj));
}
$(document).ready(function(e){

    $('.btn-attribute-add').on('click',function(){
      $(".btn-attribute-add").prop("disabled", true);

      var resourceAttributes = $('.resource-attribute');
      var n = resourceAttributes.length + 1;
      // console.log(n);

      ckan.sandbox().client.getTemplate('resource_attribute.html', {n: n})
       .done(function (data) {
         $('#resource-attributes-container').prepend(data);
         $(".btn-attribute-add").prop("disabled", false);
       });
    });

    $('#resource-attributes-container').on('click', '.btn-attribute-remove', function(e){
        $(this).closest('.resource-attribute').remove();
    });

    var items=$('.resource-attribute').toArray();
    items.reverse();
    $.each(items,function(){
       $("#resource-attributes-container").append(this);
    });
});
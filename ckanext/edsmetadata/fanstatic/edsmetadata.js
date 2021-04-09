/*
Copyright (c) 2018 Keitaro AB

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

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
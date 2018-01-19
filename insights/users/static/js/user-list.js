(function () {
    $.fn.dataTable.Buttons.defaults.dom.button.className = 'btn';
    $('.users-list').DataTable({
      scrollX: true,
      dom:
        "<'row'<'col-sm-12'f>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row bottom-table-toolbar'<'col-sm-4'B><'col-sm-8 text-right'i p>>",
        // "<'row'<'col-sm-4'l><'col-sm-4 text-center'B><'col-sm-4'f>>" +
        // "<'row'<'col-sm-12'tr>>" +
        // "<'row'<'col-sm-5'i><'col-sm-7'p>>",
      buttons: [{
        text: 'Add User',
        className: 'btn-primary',
        action: function (e, dt, node, config) {
          window.location.href = $('.users-list').data('add_user_url');
        }
      }],
      language: {
        search: '',
        searchPlaceholder: 'Search users ...'
      },
      fnDrawCallback: function (oSettings) {
        // apply tooltip every time because of paging
        $('[title]').tooltip({container: 'body'})

        // this hack is required for dataTable to resize top header properly
        // after initial load
        setTimeout(function () { $(window).resize(); }, 1000);
      },
      order: [ [ $('th.default-sort').index(),  'asc' ] ]
    });
})();

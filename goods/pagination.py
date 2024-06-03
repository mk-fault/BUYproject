from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

class GoodsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000


    def get_paginated_response(self, data):
        return Response({
            'msg': 'ok',
            'data': {
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data
            },
            'code': status.HTTP_200_OK
        })
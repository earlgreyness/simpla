
var app = angular.module('simplaApp', []);

var baseController = function ($scope, $http, $window, $q) {

    $scope.product = {};

    var serverErrorHandler = function (response) {
        console.log(response.data);
    };

    var loadProduct = function (id) {
        var config = {params: {id: id}};
        return $http.get('/api/product', config).then(function (response) {
            $scope.product = response.data['product'];
            return true;
        }, function (response) {
            serverErrorHandler(response);
            return $q.reject('No point continuing.');
        });
    };

    var getIdFromUrl = function (url) {
        var id = parseInt(url.split('/')[2]);
        return isNaN(id) ? null : id;
    };

    $scope.fixChecking = function(id) {
        for (i = 0; i < $scope.product.groups.length; i++) {
            if ($scope.product.groups[i].parent.id === id) {
                console.log('Found it!');
                for (j = 0; j < $scope.product.groups[i].children.length; j++) {
                    $scope.product.groups[i].children[j].present = $scope.product.groups[i].parent.present;
                }
                break;
            }
        }
    };

    $scope.initObject = function () {
        var the_id = getIdFromUrl($window.location.pathname);
        p = $q.when($scope.product);
        p = p.then( function () { return loadProduct(the_id); } );
    };


};

app.controller('productController', function($scope, $injector) {
    $injector.invoke(baseController, this, {$scope: $scope});
    $scope.initObject();
});

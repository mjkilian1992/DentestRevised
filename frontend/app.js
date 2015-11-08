var app = angular.module('dentest', ['ui.bootstrap', 'ui.utils', 'ngRoute','ngCookies', 'ngAnimate','ui-notification', 'auth', 'questions', 'globalConstants']);

angular.module('dentest').config(['$routeProvider','$locationProvider','NotificationProvider',
    function($routeProvider,$locationProvider,NotificationProvider) {

    /* -----------------ROUTING ----------------------*/
    /*------------------Routes------------------------*/
    $routeProvider.when('/',{templateUrl: 'partial/home-screen-partial/home-screen-partial.html'});

    /* Add New Routes Above */
    $routeProvider.otherwise({redirectTo:'/'});
    /*------------------HTML5 Mode Conf---------------*/
    $locationProvider.html5Mode(true);
    $locationProvider.hashPrefix('!');


    /*-----------------Notification Cong------------*/
    NotificationProvider.setOptions({
        delay: 10000,
        startTop: 60,
        startRight: 10,
        verticalSpacing: 20,
        horizontalSpacing: 20,
        positionX: 'left',
        positionY: 'top'
    });

}]);

//================================================RESTRICT ROUTING FOR ROUTE WHICH REQUIRE LOGIN======================/
angular.module('dentest').run(['$rootScope','$location','RestfulAuthService',
    function($rootScope,$location,RestfulAuthService){
        //intercepts when a user tries to access restricted routes
        $rootScope.$on('$routeChangeStart', function (event, next) {
            var userAuthenticated = RestfulAuthService.is_logged_in(); /* Check if the user is logged in */
            if (!userAuthenticated && next.restricted) {
                $location.path('/signup');
            }
        });
    }
]);

angular.module('dentest').run(function($rootScope) {

    $rootScope.safeApply = function(fn) {
        var phase = $rootScope.$$phase;
        if (phase === '$apply' || phase === '$digest') {
            if (fn && (typeof(fn) === 'function')) {
                fn();
            }
        } else {
            this.$apply(fn);
        }
    };

});


// Configure http to use cors (for testing purposes)

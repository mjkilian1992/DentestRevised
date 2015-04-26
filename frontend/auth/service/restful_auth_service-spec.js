'use_strict';

describe('RestfulAuthService',function(){
    beforeEach(module('dentest'));
    
     //Test Data
    var bronze_user = {
        username:'testBronze',
        email:'test.bronze@fake.com',
        first_name:'Joe',
        last_name:'Bloggs',   
    };

    var bronze_password = 'zZ123##<>';
    var bronze_token = '1234567890qwertyuiop';
    var bronze_login_response = jQuery.extend(true,{token:bronze_token},bronze_user); //add token (not in user profile)
    var bronze_reg_details = jQuery.extend(true,{password1:'AsDf1234{}',password2:'AsDf1234{}'},bronze_user); //add passwords
    
    
    var authservice,mockBackend,baseURL;
    
    //Defines an errors list and callback function as we would expect a controller to have
     var errors = null;
        var error_handler = function(error_list){
            errors = error_list;
        };
    beforeEach(inject(function($httpBackend,RestfulAuthService,REST_BASE_URL){
        baseURL = REST_BASE_URL
        errors = null;
        mockBackend = $httpBackend;
        spyOn(RestfulAuthService,'login').andCallThrough();
        spyOn(RestfulAuthService,'logout').andCallThrough();
        authservice = RestfulAuthService;
    }));

    afterEach(function(){
        mockBackend.verifyNoOutstandingExpectation();
        mockBackend.verifyNoOutstandingRequest();
    });
    
    //========================================LOGIN======================================================================
    describe('Logging in',function(){
 
        it('should make a request to the correct api endpoint',function(){
            mockBackend.expectPOST(baseURL + '/login/').respond(200,{});
            authservice.login('test','test',error_handler);
            mockBackend.flush();
        });
        it("should store the users details and set the Authorization header with the token if they have the correct credentials",inject(function($http){
            mockBackend.expectPOST(baseURL + '/login/').respond(200,bronze_login_response);
            authservice.login('testBronze','zZ123##<>',error_handler);
            mockBackend.flush();
            expect(authservice.is_logged_in()).toBe(true);
            expect(authservice.user_profile()).toEqual(bronze_user);
            expect(errors).toEqual({});
            //expectation works because the header is set on the REAL http service
            expect($http.defaults.headers.common['Authorization']).toEqual(bronze_token);
        }));
        it("should return a list of errors if the credentials were incorrect",function(){
            var serializer_errors = {'non_field_errors':'Unable to login with credentials provided'}
            mockBackend.expectPOST(baseURL + '/login/').respond(401,serializer_errors);
            authservice.login('testBronze','gibberish',error_handler);
            mockBackend.flush();
            expect(authservice.is_logged_in()).toBe(false);
            expect(errors).toEqual(serializer_errors);
        });   
    });
    
    //====================================LOGOUT===========================================================================
    describe('Logging out',function(){
        it("should clear the users profile if they are logged in (relies on login working)",inject(function($http){
            mockBackend.expectPOST(baseURL + '/login/').respond(200,bronze_login_response);
            authservice.login('testBronze','zZ123##<>',error_handler);
            mockBackend.flush()
            //Check preconditions
            expect(authservice.user_profile()).toEqual(bronze_user);
            expect($http.defaults.headers.common['Authorization']).toEqual(bronze_token);
            //Now check logout clears info
            authservice.logout();
            expect(authservice.is_logged_in()).toBe(false);
            expect(authservice.user_profile()).toEqual({username:null,email:null,first_name:null,last_name:null});
            expect($http.defaults.headers.common['Authorization']).toEqual(null);
        }));
    
    });
    
    //=================================REGISTRATION==========================================================================
    describe('Registration',function(){
        it("should make a request to the correct api endpoint",function(){
            mockBackend.expectPOST(baseURL + '/register/').respond(400,{}); //cause an error so login is not called
            authservice.register(bronze_reg_details,error_handler);
            mockBackend.flush();
        });
        
        it("should log the user in if successful (relies on login)",function(){
            mockBackend.expectPOST(baseURL + '/register/').respond(201,{});
            mockBackend.expectPOST(baseURL + '/login/').respond(200,bronze_login_response);
            authservice.register(bronze_reg_details,error_handler);
            mockBackend.flush();
            expect(authservice.login).toHaveBeenCalledWith('testBronze','AsDf1234{}',error_handler);
            expect(authservice.user_profile()).toEqual(bronze_user);
        });
        
        it("should return errors if invalid details were provided",function(){
            mockBackend.expectPOST(baseURL + '/register/').respond(400,{'errors':[]});
            authservice.register(bronze_reg_details,error_handler);
            mockBackend.flush();
            expect(authservice.login).not.toHaveBeenCalled();
            expect(errors).toEqual({'errors':[]});
        });
    });
    
    //==================================PASSWORD RESET========================================================================
    describe('Password Reset',function(){
        it("should make a request to the correct api endpoint",function(){
            mockBackend.expectPOST(baseURL + '/password_reset/').respond(201,{});
            authservice.password_reset(bronze_user,error_handler);
            mockBackend.flush();
        });
        
        it("should return error if invalid details were provided",function(){
            mockBackend.expectPOST(baseURL + '/password_reset/').respond(401,{'errors':[]});
            authservice.password_reset(bronze_user,error_handler);
            mockBackend.flush();
            expect(errors).toEqual({'errors':[]});
        });
    });
    
    //==================================PASSWORD RESET CONFIRM================================================================
    describe('Password Reset Confirm',function(){
        var reset_info = {
            username:'testBronze',
            key:'1234567890',
            password1:'1337:@H4XX0Rz',
            password2:'1337:@H4XX0Rz',
        };
        it('should make a request to the correct api endpoint',function(){
            mockBackend.expectPOST(baseURL + '/password_reset_confirm/').respond(400,{}); //fake error to avoid login
            authservice.password_reset_confirm(reset_info,error_handler);
            mockBackend.flush();
        });
        
        it("should log the user in if successful (relies on login)",function(){
            mockBackend.expectPOST(baseURL + '/password_reset_confirm/').respond(200,{});
            mockBackend.expectPOST(baseURL + '/login/').respond(200,bronze_login_response);
            authservice.password_reset_confirm(reset_info,error_handler);
            mockBackend.flush();
            expect(authservice.login).toHaveBeenCalledWith('testBronze','1337:@H4XX0Rz',error_handler);
            expect(authservice.user_profile()).toEqual(bronze_user);
        });
        
        it('should return errors if invalid details were provided',function(){
            mockBackend.expectPOST(baseURL + '/password_reset_confirm/').respond(400,{'errors':[]});
            authservice.password_reset_confirm(reset_info,error_handler);
            mockBackend.flush();
            expect(errors).toEqual({'errors':[]});
        });
    });
    
    //===================================EMAIL ACTIVATION======================================================================
     describe('Email Activation',function(){
        var reset_info = {
            username:'testBronze',
            key:'1234567890',
        };
        it('should make a request to the correct api endpoint',function(){
            mockBackend.expectPOST(baseURL + '/confirm_email/').respond(200,{});
            authservice.confirm_email(reset_info,error_handler);
            mockBackend.flush();
        });
        it('should return errors if invalid details were provided',function(){
            mockBackend.expectPOST(baseURL + '/confirm_email/').respond(400,{'errors':[]});
            authservice.confirm_email(reset_info,error_handler);
            mockBackend.flush();
            expect(errors).toEqual({'errors':[]});
        });
    });
    
    //==========================================PROFILE UPDATE=================================================================
    describe('Profile Update',function(){
        it('should make a request to the correct api endpoint',function(){
            mockBackend.expectPUT(baseURL + '/update_profile/').respond(200,{});
            authservice.update_profile(bronze_user,error_handler);
            mockBackend.flush();
        });
        
        it('should return errors if invalid details were provided',function(){
            mockBackend.expectPUT(baseURL + '/update_profile/').respond(400,{'errors':[]});
            authservice.update_profile(bronze_user,error_handler);
            mockBackend.flush();
            expect(errors).toEqual({'errors':[]});
        });
        
        it('should log the user out',function(){
            mockBackend.expectPUT(baseURL + '/update_profile/').respond(200,{});
            authservice.update_profile(bronze_user,error_handler);
            mockBackend.flush()
            expect(authservice.logout).toHaveBeenCalled();
            expect(authservice.is_logged_in()).toBe(false);
        }); 
    });
            
});

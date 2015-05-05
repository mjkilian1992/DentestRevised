angular.module('questions').service('QuestionService',['$http','REST_BASE_URL', function($http,REST_BASE_URL) {
    var self = this;
    
    var build_query_params= function(page_number,page_size){
    /**Convenience method for building query parameters*/
        return {
            format:'json',
            page:page_number,
            page_size:page_size,
        };
    };
    //====================PAGINATION CONFIG AND STATE=============================
    var page_size = 50; //Can replace this with clever method later
    
    var pagination_info = {
        no_of_pages:null,
        current_page_number:null,
        next_page_number:null,
        previous_page_number:null,
        next_page_link:null,
        previous_page_link:null,
    };
    
    /**====================PAGINATION METHODS===================================*/
    
    self.get_page_size = function(){
        return page_size;
    };
    
    self.set_page_size = function(size){
        page_size = size;
    };
    
    self.get_pagination_info = function(){
        return pagination_info;
    };
    
    self.clear_pagination_info = function(){
        pagination_info.no_of_pages = null;
        pagination_info.current_page_number = null;
	    pagination_info.next_page_number = null;
	    pagination_info.next_page_link = null;
	    pagination_info.previous_page_number = null;
	    pagination_info.previous_page_link = null;
	};
	
	self.build_pagination_info = function(request_page_number,response){
	    pagination_info.next_page_link = response.next;
	    pagination_info.previous_page_link = response.previous;
        pagination_info.current_page_number = request_page_number;	
	    if(response.next == null){
	        pagination_info.next_page_number = null;
	    }else{
	        pagination_info.next_page_number = request_page_number + 1;
	    }
	    if(response.previous == null){
	        pagination_info.previous_page_number = null;
	    }else{
	        pagination_info.previous_page_number = request_page_number - 1;
	    }
	    pagination_info.no_of_pages = Math.ceil(Number(response.count) / page_size);
	};
	
	self.next_page = function(result_handler){
	     if (pagination_info.next_page_number == null){
	        result_handler(null);
	     }else{
	        $http.get(pagination_info.next_page_link)
	        .then(function(response){ //success
	            self.build_pagination_info(pagination_info.current_page_number + 1,response.data);       
	            result_handler({data:response.data,errors:{}});
	         },function(response){ //failure
	            result_handler({data:{},errors:response.data});
	        });
	     }
	     
	};
	
	self.previous_page = function(result_handler){
	     if (pagination_info.previous_page_number == null){
	        result_handler(null);
	     }else{
	        $http.get(pagination_info.previous_page_link)
	        .then(function(response){ //success
	            self.build_pagination_info(pagination_info.current_page_number - 1,response.data);   
	            result_handler({data:response.data,errors:{}});
	         },function(response){ //failure
	            result_handler({data:{},errors:response.data});
	        });
	     }
	};
	
	//========================API CONFIG==============================
	var api_urls = {
	    topics: REST_BASE_URL + '/topics/',
	    subtopics: REST_BASE_URL + '/subtopics/',
	    questions: REST_BASE_URL + '/questions/',
	    questions_by_topic: REST_BASE_URL + '/questions/by_topic/',
	    questions_by_subtopic: REST_BASE_URL + '/questions/by_subtopic/',
	    question_by_id: REST_BASE_URL + '/questions/question_number/',
	};
	
	//========================GET TOPICS==============================
	self.getTopics = function(page_number,result_handler){
	    $http.get(api_urls.topics,{params:build_query_params(page_number,page_size)})
	    .then(function(response){ //success
	            self.build_pagination_info(page_number,response.data);   
	            result_handler({data:response.data,errors:{}});
	         },function(response){ //failure
	            result_handler({data:{},errors:response.data});
	        });
	};
	
	//========================GET SUBTOPICS===========================
	self.getSubtopics = function(page_number,result_handler){
	    $http.get(api_urls.subtopics,{params:build_query_params(page_number,page_size)})
	    .then(function(response){ //success
	            self.build_pagination_info(page_number,response.data);   
	            result_handler({data:response.data,errors:{}});
	         },function(response){ //failure
	            result_handler({data:{},errors:response.data});
	        });
	};
	
	//=========================GET QUESTIONS==========================
	self.getQuestions = function(page_number,result_handler){
	    $http.get(api_urls.questions,{params:build_query_params(page_number,page_size)})
	     .then(function(response){ //success
	            self.build_pagination_info(page_number,response.data);   
	            result_handler({data:response.data,errors:{}});
	         },function(response){ //failure
	            result_handler({data:{},errors:response.data});
	        });
	};
	
	//=======================GET QUESTIONS BY TOPIC====================
	self.getQuestionsByTopic = function(page_number,topic,result_handler){
	    $http.get(api_urls.questions_by_topic + topic + '/',{params:build_query_params(page_number,page_size)})
	     .then(function(response){ //success
	            self.build_pagination_info(page_number,response.data);   
	            result_handler({data:response.data,errors:{}});
	         },function(response){ //failure
	            result_handler({data:{},errors:response.data});
	        });
	};
	
	//=======================GET QUESTIONS BY SUBTOPIC=================
	self.getQuestionsBySubtopic = function(page_number,topic,subtopic,result_handler){
	    $http.get(api_urls.questions_by_subtopic + topic + '/' +subtopic + '/',
	        {params:build_query_params(page_number,page_size)})
	     .then(function(response){ //success
	            self.build_pagination_info(page_number,response.data);   
	            result_handler({data:response.data,errors:{}});
	         },function(response){ //failure
	            result_handler({data:{},errors:response.data});
	        });
	};
	
	//=======================GET QUESTION BY ID========================
	self.getQuestionByID = function(question_number,result_handler){
	    $http.get(api_urls.question_by_id + question_number + '/',
	        {params:{format:'json'}})
	    .then(function(response){ //success  
	            result_handler({data:response.data,errors:{}});
	         },function(response){ //failure
	            result_handler({data:{},errors:response.data});
	        });
	};
	        
	
}]);

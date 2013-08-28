$( document ).ready(function() {
    //This function is called once everything on the page is loaded and we're ready to execute javascript
    console.log( "document loaded" );

    //Set default values of input
    $( "#step" ).val(1)
    $( "#time" ).val(100)

    //This holds the data to be rendered if a job is selected
    // key:jobid
    // v: html to be rendered
    jobs = {}

    //This variable will be used to hold whatever model is of interest
    model = null

    //Set up event handlers
    setup();

    //New job button is disabled at beginning if no file automatically selected
    if(!$( "#image-file" ).prop('files')[0])
    {
        $( "#newjob" ).prop('disabled', true)
    }
    else
    {
        $( "#image-file" ).trigger('change')
        $( "#newjob" ).prop('disabled', false)
    }

    //Load up all run jobs
    refresh();
});

var setup = function()
{
    //When the image-file input changes, go ahead and get the file uploading
    $( "#image-file" ).change(
        function(event)
        {
            var file = $( "#image-file" ).prop('files')[0];
            var read = new FileReader();
            
            model = null

            $( "#newjob" ).prop('disabled', true)

            read.onload = 
                function(event)
                {
                    model = event.target.result
                    $( "#newjob" ).prop('disabled', false)
                };

            read.readAsText(file)
        }
    )

    //Refresh joblist on req.

    refresh = function(event)
        {
            //Send a GET request to the server (with no data, it only knows to return one thing)
            $.ajax({type : "GET",
                    url : "http://localhost:8084",
                    //The client and server can be on different computers
                    crossDomain: true,
                    //This is the return format
                    dataType : "json",
                    //On success, this function is called with the return data (already parsed into a json object as we ask'd above
                    success : function(dataObj) {
                        // We need to handle two things with this call:
                        //   1. Parse the received JSON object and create HTML divs with visualization info for each set of Job data received
                        //   2. Create links in the appropriate place to make the HTML visualization divs visible
                        
                        // Clear out the current links
                        $( "#running_jobs" ).html('');
                        $( "#finished_jobs" ).html('');

                        // For each job info received...
                        // dataObj[0] = { jobid: #,
                        //                args: (...),
                        //                plots: [none if not done, list of img urls otherwise] }
                        for(var jobid in dataObj)
                        {
                            html = '<h4>Job ' + jobid + '</h4>' +
                                'model : ' + ((dataObj[jobid].args.model.length < 100) ? dataObj[i].args.model : '<i>model string too long</i>') + '<br>' +
                                'time : ' + dataObj[jobid].args.time + '<br>' +
                                'increment : ' + dataObj[jobid].args.increment + '<hr>' +
                                'Renderings:' + '<br>';

                            // When a .jobhtml link is clicked, call this function to make the appropriate div visible
                            var clicked = function(event)
                            {
                                jobid = $.data(event.target, 'jobid' )
                                $( ".jobhtml" ).hide()
                                $( "#jobhtml" + jobid ).show()
                            }

                            // Search for the HTML div that contains the to-be-rendered data
                            var jobhtml_selector = $( "#jobhtml" + jobid )

                            // If it doesn't exist, create it
                            if(!jobhtml_selector[0])
                            {
                                jobhtml_selector = $('<div class = "jobhtml" id="jobhtml' + jobid + '" />').appendTo( "#windows_html" )
                            }

                            // If there are plots listed, the job is finished, and the full output should be rendered
                            if(dataObj[jobid].plots)
                            {
                                for(var ii = 0; ii < dataObj[jobid].plots.length; ii++)
                                {
                                    html = html + '<img width=400 src = \'' + dataObj[jobid].plots[ii] + '\' />';
                                }

                                // Add the link to the #finished jobs links, set the callback, select the element specifically
                                var element = $('<a class="joblink" id="link' + jobid + '" href = "#">Job_' + jobid + '</a>').appendTo("#finished_jobs").click(clicked)[0]

                                $( "#finished_jobs" ).append(" ")

                                // Tie the jobid as jquery data to the link. When the link is clicked, it can access this data
                                $.data( element, 'jobid', jobid )
                            }
                            else // Otherwise just say the job is still running
                            {
                                html = html + 'Still running'

                                // Add the link to the #finished jobs links, set the callback, select the element specifically
                                var element = $('<a class="joblink" id="link' + jobid + '" href = "#">Job_' + jobid + '</a>').appendTo("#running_jobs").click(clicked)[0]
                                $( "#running_jobs" ).append(" ")

                                // Tie the jobid as jquery data to the link. When the link is clicked, it can access this data
                                $.data(element, 'jobid', jobid )
                            }

                            // Hide the newly created html block (we'll only show it when it gets clicked)
                            jobhtml_selector.hide()

                            // Fill it with html!
                            jobhtml_selector.html(html)
                        }
                    }
                   });
        }

    $( "#refresh" ).click(refresh)

    $( "#newjob" ).click( function(event) {
        //Get the inputs
        time = $( "#time" ).val()
        increment = $( "#step" ).val()

        $.ajax({type : "POST",
                url : "http://localhost:8084",
                crossDomain: true,
                data : { request : JSON.stringify({model : model, time : time, increment : increment }) },
                dataType : "json",
                success : function(data) {
                    console.log(data.status)
                }
               });

        refresh();
    });
}

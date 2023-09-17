<?php
    require 'php/templates/header.php';
?>
<script src="js/pialert_common.js"></script>
<div id="donationsPage" class="content-wrapper">
    <!-- Content header--------------------------------------------------------- -->
    <section class="content-header">
        <h1 id="pageTitle">
            <i class="fa fa-heart"></i>                
        </h1>
    </section>

    <!-- Main content ---------------------------------------------------------- -->
    <section class="content donations">	
        <div id="donationsText" class="box box-solid"></div> 
        <div class="content-header">
            <h3 class="box-title " id="donationsPlatforms"></h3>
        </div> 
        <div class="box box-solid">
            <div class="box-body">
                <div class="col-sm-2">
                    <a target="_blank" href="https://github.com/sponsors/jokob-sk">
                        <img alt="Sponsor Me on GitHub" src="https://i.imgur.com/X6p5ACK.png" width="150px">
                    </a>
                </div>
                <div class="col-sm-2">
                    <a target="_blank" href="https://www.buymeacoffee.com/jokobsk">
                        <img alt="Buy Me A Coffee" src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" width="117px" height="30px">
                    </a>
                </div>
                <div class="col-sm-2">
                    <a target="_blank" href="https://www.patreon.com/user?u=84385063">
                        <img alt="Support me on patreon" src="https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Patreon_logo_with_wordmark.svg/512px-Patreon_logo_with_wordmark.svg.png" width="117px">
                    </a>
                </div>
            </div>
        </div>        
        <div class="content-header">
            <h3 class="box-title " id="donationsOthers"></h3>
        </div>
        <div class="box box-solid">
            <div class="box-body">
                <div class="col-sm-12">
                    <ul>
                        <li>Bitcoin: <code>1N8tupjeCK12qRVU2XrV17WvKK7LCawyZM</code></li>
                        <li>Ethereum: <code>0x6e2749Cb42F4411bc98501406BdcD82244e3f9C7</code></li>
                    </ul>
                </div>
            </div>
        </div>
        <div>
    </section>

</div> <!-- End of class="content-wrapper"  -->

<script>
    function init()
    {        
        $("#donationsText").html(getString("Donations_Text"))
        $("#pageTitle").append(getString("Donations_Title"))
        $("#donationsPlatforms").append(getString("Donations_Platforms"))
        $("#donationsOthers").append(getString("Donations_Others"))
    }

    init();
</script>

<?php
        require 'php/templates/footer.php';
?>
// ==UserScript==
// @name        Stack Exchange Review Helper
// @namespace   http://www.ozmonet.com/
// @version     0.4
// @description Auto-refresher for Stack Exchange style reviews
// @match       http://*.com/review/first-posts
// @match       http://*.com/review/late-answers
// @copyright   2013
// ==/UserScript==

function CheckReviewPosts()
{
    var content = document.body.innerHTML;
    var position = content.search("There are no items for you to review.");
    if (position == -1)
    {
        position = content.search(/This is [the|a]/);
        if (position != -1)
        {
            var snd = new Audio("http://fsa.zedge.net/content/7/8/7/4/4-1368013-78740453.mp3"); // buffers automatically when created
            snd.play();

            var link = document.createElement('link');
            link.type = 'image/x-icon';
            link.rel  = 'shortcut icon';
            link.href = 'data:image/x-icon;base64,' +
                'AAABAAEAEBAAAAAAAABoBQAAFgAAACgAAAAQAAAAIAAAAAEACAAAAAAAAAEAA' +
                'AAAAAAAAAAAAAEAAAAAAAAAAAAANaC5ACsrKwAWueAAKtTmACWtvwAUr9MA1d' +
                'nZALzMzQDZ2dkA3+bmABfB4wB1s7wAfcTGABbJ5gAgKy0Ax+PoADQ0NAAUQkg' +
                'AMN3vABam1QAWxOQAw+HmABmrxwBawMMAgLu/AC/o8gDG4+kAxM/PAKzCwwDE' +
                '4ecAFbDTACvb7gDY3t4AFr/jABnU6gAWwuMAwt/lAC3a6QDe4OEA2NzcAOnr6' +
                'wAWuuEAwN7gAC3m8QDY3t8Asc/RAMHd4wAWyuYAF8rmACa90AAWtd8ARLvEAM' +
                'jm6wAp0NUAF6TFACy5wwDG5OkAIiwuABS21QDI5OkAv9nfAKDLzgAWxeUAF7D' +
                'eACza4wA6tb4AFsDjADS9yQCRt70AF6vcANLj5AAu7PMAFtDoACIiIgAWu+EA' +
                'F6baADDk8QAn3+8ANEBBABaz3wDc398Awd7jADQ8PABXq7kAIJS6ABbD5AC/3' +
                'OEAmsHDAN3d3QAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAAAAAAAAAKFdSFjk1PBAbHiUvPVEAACE3AypLBjo6U' +
                'EBGTFUnAAAADAskVjsPDyozQBRFAAAAAC0FMTAOFxdDSzMBCQAAAAAAPgQjSR' +
                'ISPyIfHQAAAAAAAClCTU5KSjAVVAAAAAAAAAAAK0EaAgIgMhwAAAAAAAAAAAA' +
                'YSBERExkAAAAAAAAAAAAARzZTT0QHAAAAAAAAAAAAAAANLCZYAAAAAAAAAAAA' +
                'AAAACjg0WQAAAAAAAAAAAAAAAAAuCAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA' +
                'AAAAAAAAAAAAAAAAAAAAP//AAD//wAAgAEAAIABAADAAwAAwAMAAOAHAADgDw' +
                'AA8A8AAPgfAAD4HwAA/D8AAPw/AAD+fwAA//8AAP//AAA=';
            document.getElementsByTagName('head')[0].appendChild(link);
        }
    }
    else
    {
        // reload page
        window.location.reload();
    }
}

setTimeout(CheckReviewPosts, 3500);

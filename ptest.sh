#!/bin/bash

set -x  # Enable command tracing

DEBUG=true printf '# Test\n$E=mc^2$' | smart-pandoc-debugger 2>&1 
echo "(Expectation: no errors.)"

DEBUG=true printf 'This is some *invalid markdown that Pandoc might choke on, like an unclosed emphasis or a bizarre table.' | smart-pandoc-debugger 2>&1 
echo "(Expectation: Miner should detect and provide a fix.)"

DEBUG=true printf '# Good Markdown\n\nThis will produce TeX with an undefined command:\n\n$\\nonexistentcommand$' | smart-pandoc-debugger 2>&1 
echo "(Expectation: md->tex ok, tex->pdf fails, Oracle provides a fix.)"

set +x  # Disable command tracing

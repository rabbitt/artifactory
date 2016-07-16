
module ProjectHooks
  extend self

  def root
    Pathname.new(__FILE__).realpath.dirname
  end

  def configs
    root.join('configs')
  end

  def lib
    root.join('lib')
  end
end

require 'formatting'
require 'commit-messages'

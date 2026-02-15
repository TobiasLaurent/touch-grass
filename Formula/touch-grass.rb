class TouchGrass < Formula
  include Language::Python::Virtualenv

  desc "CLI tool that checks if it's safe to go outside and touch grass"
  homepage "https://github.com/tobiaslaurent/touch-grass"
  url "https://files.pythonhosted.org/packages/source/t/touch-grass/touch_grass-0.1.0.tar.gz"
  sha256 "PLACEHOLDER"
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "touch-grass", shell_output("#{bin}/touch-grass --help")
  end
end

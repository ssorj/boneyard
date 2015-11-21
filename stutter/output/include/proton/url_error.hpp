namespace proton {

class url_error {
  public:
    url_error() {
      number = new int;
      *number = 0;
    }
  private:
    int * number;
};

}
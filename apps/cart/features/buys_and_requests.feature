Feature: Rocking with lettuce and django

    Scenario: Fill database
        Given I have the following users in my database:
            | username     | email                 | first_name | last_name  |
            | Paul         | paul@gmail.com        | Paul       | Gilham     |
            | Anton        | anton@gmail.com       | Anton      | Romanovich |
            | Alexei       | alexei@gmail.com      | Alexei     | Selivanov  |
            | Semeyon      | semeyon@gmail.com     | Semeyon    | Svetliy    |
        
        Given I have the following stores in my database:
            | name         | user  | category    |
            | Cool Store   | Paul  | Test Stores |
            | Bad Store    | Anton | Test Stores |
        
        Given I have the following discount models in "Cool Store":
            | name           | for_additional_item | for_additional_buyer | lower_bound |
            | DiscountModel1 | 5                   | 5                    | 50          |

        Given I have the following discount models in "Bad Store":
            | name           | for_additional_item | for_additional_buyer | lower_bound |
            | DiscountModel2 | 6                   | 7                    | 50          |

        Given I have the following items in "Cool Store" grouped together with "DiscountModel1":
            | name         | price  |
            | iPad         | 400.00 |
            | iPhone       | 200.00 |

        Given I have the following items in "Bad Store" grouped together with "DiscountModel2":
            | name         | price  |
            | Kindle       | 99.00  |

    Scenario: Create Social Buy
        Given I'm logged in as Alexei.
        
        Given To buy 1 "iPad" I create a Social Buy that finishes in 24 hours. Let's call it Buy1.
        Then In cart I see the only following Social Buys:
            | name |
            | Buy1 |
        And I see that Buy1 contains 1 "iPad".
        And I see Buy1 on "iPad" item page and it's inactive.
        And I see Buy1 on "iPhone" item page and it's inactive.
        But I don't see any Social Buy on "Kindle" item page.
        
        Given I'm logged in as Anton.
        Then I don't see any Social Buy on "iPad" item page.

    Scenario: Delete Social Buy
        Given To buy 1 "Kindle" I create a Social Buy that finishes in 24 hours. Let's call it KindleBuy.
        Then In cart I see the only following Social Buys:
            | name      |
            | KindleBuy |
        Given I put 0 "Kindle" to KindleBuy.
        Then In cart I see no Social Buys.

    Scenario: Create Shipping Request
        Given I'm logged in as Alexei.
        
        Given I request shipping for Buy1.
        Then In cart I see no Social Buys.
        But In cart I see pending Shipping Requests only for the following Social Buys:
            | name |
            | Buy1 |

        Given To buy 1 "iPhone" I create a Social Buy that finishes in 48 hours. Let's call it Buy2.
        Then In cart I see the only following Social Buys:
            | name |
            | Buy2 |
        Then I cancel pending Shipping Request for Buy1.
        
        Then In cart I see the only following Social Buys:
            | name |
            | Buy1 |
            | Buy2 |
        And In cart I see no pending Shipping Requests.
    
   Scenario: Merge tags after Shipping Request cancellation
        Given I request shipping for Buy1.
        Then In cart I see the only following Social Buys:
            | name |
            | Buy2 |
        Given I put 1 "iPad" to Buy1.
        And I cancel pending Shipping Request for Buy1.
        Then In cart I see the only following Social Buys:
            | name |
            | Buy1 |
            | Buy2 |
        And I see that Buy1 contains 2 "iPad".
    
   Scenario: Merge tags after Pickup Request cancellation
        Given I request pickup for Buy1.
        Then In cart I see the only following Social Buys:
            | name |
            | Buy2 |
        And In cart I see Pickup Requests only for the following Social Buys:
            | name |
            | Buy1 |
        Given I put 100 "iPad" to Buy1.
        And I cancel pending Pickup Request for Buy1.
        Then In cart I see the only following Social Buys:
            | name |
            | Buy1 |
            | Buy2 |
        And I see that Buy1 contains 102 "iPad".
